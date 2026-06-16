import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.blocking_reason import BlockingReason
from database.models.outbox import OutboxEvent
from database.models.tickets.ticket import Ticket, TicketStatus
from tests.integration.conftest import (
	B2B_SERVICE_KEY_HEADERS,
	TicketFixtureData,
	auth_headers,
	product_deleted_body,
	product_edited_body,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _block(
	client: AsyncClient,
	ticket_id: uuid.UUID,
	reason_ids: list[uuid.UUID],
	headers: dict[str, str],
	comment: str = "Counterfeit confirmed",
) -> int:
	response = await client.post(
		f"/api/v1/tickets/{ticket_id}/block",
		headers=headers,
		json={
			"blocking_reason_ids": [str(reason_id) for reason_id in reason_ids],
			"comment": comment,
			"field_reports": [],
		},
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


async def _hard_block_ticket(
	client: AsyncClient,
	db_session: AsyncSession,
	ticket: Ticket,
	moderator_id: uuid.UUID,
	reason: BlockingReason,
) -> Ticket:
	headers = await auth_headers(moderator_id, db_session)
	status_code = await _block(client, ticket.id, [reason.id], headers)
	assert status_code == 200
	await db_session.refresh(ticket)
	return ticket


async def test_hard_block_transitions_to_terminal_and_emits_event(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	hard_block_reason: BlockingReason,
) -> None:
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _block(
		client,
		in_review_ticket.id,
		[hard_block_reason.id],
		headers,
	)
	assert status_code == 200

	await db_session.refresh(in_review_ticket)
	assert in_review_ticket.status == TicketStatus.HARD_BLOCKED
	assert in_review_ticket.decision_at is not None
	assert in_review_ticket.blocking_reason_id == hard_block_reason.id

	outbox = await _latest_outbox_event(db_session, ticket_fixture_data.product_id)
	assert outbox is not None
	assert outbox.routing_key == "b2b.moderation.result"
	assert outbox.payload["event_type"] == "BLOCKED"
	assert outbox.payload["product_id"] == str(ticket_fixture_data.product_id)
	assert outbox.payload["moderator_id"] == str(ticket_fixture_data.moderator_id)


async def test_hard_block_event_carries_hard_block_true(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	hard_block_reason: BlockingReason,
) -> None:
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _block(
		client,
		in_review_ticket.id,
		[hard_block_reason.id],
		headers,
	)
	assert status_code == 200

	outbox = await _latest_outbox_event(db_session, ticket_fixture_data.product_id)
	assert outbox is not None
	assert outbox.payload["hard_block"] is True
	assert outbox.payload["blocking_reason_id"] == str(hard_block_reason.id)


async def test_any_modify_on_hard_blocked_returns_403(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	hard_block_reason: BlockingReason,
) -> None:
	await _hard_block_ticket(
		client,
		db_session,
		in_review_ticket,
		ticket_fixture_data.moderator_id,
		hard_block_reason,
	)
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	approve_response = await client.post(
		f"/api/v1/tickets/{in_review_ticket.id}/approve",
		headers=headers,
		json={"comment": "Should fail"},
	)
	assert approve_response.status_code == 403

	block_response = await client.post(
		f"/api/v1/tickets/{in_review_ticket.id}/block",
		headers=headers,
		json={
			"blocking_reason_ids": [str(hard_block_reason.id)],
			"comment": "Should fail",
		},
	)
	assert block_response.status_code == 403


async def test_edited_event_on_hard_blocked_is_ignored(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	hard_block_reason: BlockingReason,
) -> None:
	await _hard_block_ticket(
		client,
		db_session,
		in_review_ticket,
		ticket_fixture_data.moderator_id,
		hard_block_reason,
	)
	old_updated_at = in_review_ticket.updated_at
	old_decision_at = in_review_ticket.decision_at

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

	await db_session.refresh(in_review_ticket)
	assert in_review_ticket.status == TicketStatus.HARD_BLOCKED
	assert in_review_ticket.decision_at == old_decision_at
	assert in_review_ticket.updated_at == old_updated_at


async def test_deleted_event_removes_hard_blocked(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	hard_block_reason: BlockingReason,
) -> None:
	await _hard_block_ticket(
		client,
		db_session,
		in_review_ticket,
		ticket_fixture_data.moderator_id,
		hard_block_reason,
	)

	body = product_deleted_body(ticket_fixture_data.product_id)
	response = await client.post(
		"/api/v1/b2b/events",
		headers=B2B_SERVICE_KEY_HEADERS,
		json=body,
	)
	assert response.status_code == 202

	result = await db_session.execute(
		select(Ticket).where(Ticket.id == in_review_ticket.id)
	)
	assert result.scalar_one_or_none() is None
