import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.variants import Sku
from database.models.identity.moderator import Moderator
from database.models.outbox import OutboxEvent
from database.models.tickets.ticket import Ticket, TicketStatus
from tests.integration.conftest import (
	B2B_SERVICE_KEY_HEADERS,
	TicketFixtureData,
	auth_headers,
	product_edited_body,
	sample_product_snapshot,
	seed_catalog_replica,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _approve(
	client: AsyncClient,
	ticket_id: uuid.UUID,
	headers: dict[str, str],
) -> int:
	response = await client.post(
		f"/api/v1/tickets/{ticket_id}/approve",
		headers=headers,
		json={"comment": "Looks good"},
	)
	return response.status_code


async def _latest_outbox_event(
	db_session: AsyncSession, product_id: uuid.UUID
) -> OutboxEvent | None:
	result = await db_session.execute(
		select(OutboxEvent).order_by(OutboxEvent.created_at.desc())
	)
	for event in result.scalars().all():
		if event.payload.get("product_id") == str(product_id):
			return event
	return None


async def test_approve_transitions_to_moderated_and_emits_event(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
) -> None:
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _approve(client, in_review_ticket.id, headers)
	assert status_code == 200

	await db_session.refresh(in_review_ticket)
	assert in_review_ticket.status == TicketStatus.APPROVED
	assert in_review_ticket.decision_at is not None

	outbox = await _latest_outbox_event(db_session, ticket_fixture_data.product_id)
	assert outbox is not None
	assert outbox.routing_key == "b2b.moderation.result"
	assert outbox.payload["event_type"] == "MODERATED"
	assert outbox.payload["product_id"] == str(ticket_fixture_data.product_id)
	assert outbox.payload["moderator_id"] == str(ticket_fixture_data.moderator_id)


async def test_approve_others_card_returns_403(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	other_moderator: Moderator,
) -> None:
	headers = await auth_headers(other_moderator.id, db_session)

	status_code = await _approve(client, in_review_ticket.id, headers)
	assert status_code == 403


async def test_approve_after_edited_returns_409(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
) -> None:
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)
	body = product_edited_body(
		ticket_fixture_data.product_id,
		ticket_fixture_data.seller_id,
	)
	response = await client.post(
		"/api/v1/b2b/events",
		headers=B2B_SERVICE_KEY_HEADERS,
		json=body,
	)
	assert response.status_code == 202

	status_code = await _approve(client, in_review_ticket.id, headers)
	assert status_code == 409


async def test_approve_without_sku_returns_409(
	client: AsyncClient,
	db_session: AsyncSession,
	ticket_fixture_data: TicketFixtureData,
	moderator: Moderator,
) -> None:
	_ = moderator.id
	await seed_catalog_replica(
		db_session,
		ticket_fixture_data.product_id,
		ticket_fixture_data.seller_id,
	)
	await db_session.execute(
		delete(Sku).where(Sku.product_id == ticket_fixture_data.product_id)
	)
	await db_session.commit()

	from tests.integration.conftest import persist_ticket

	ticket = await persist_ticket(
		db_session,
		product_id=ticket_fixture_data.product_id,
		seller_id=ticket_fixture_data.seller_id,
		status=TicketStatus.IN_REVIEW,
		assigned_moderator_id=ticket_fixture_data.moderator_id,
		json_after=sample_product_snapshot(
			ticket_fixture_data.product_id,
			ticket_fixture_data.seller_id,
			title="No sku snapshot",
		),
	)
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _approve(client, ticket.id, headers)
	assert status_code == 409
