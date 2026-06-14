import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.blocking_reason import BlockingReason
from database.models.identity.moderator import Moderator
from database.models.outbox import OutboxEvent
from database.models.tickets.field_report import TicketFieldReport
from database.models.tickets.ticket import Ticket, TicketStatus
from tests.integration.conftest import (
	TicketFixtureData,
	auth_headers,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _sku_id_from_ticket(ticket: Ticket) -> uuid.UUID:
	sku_id = ticket.json_after["skus"][0]["id"]
	return uuid.UUID(sku_id) if isinstance(sku_id, str) else sku_id


async def _block(
	client: AsyncClient,
	ticket_id: uuid.UUID,
	reason_ids: list[uuid.UUID],
	headers: dict[str, str],
	comment: str = "Description and photos do not match the product",
	field_reports: list[dict] | None = None,
) -> int:
	body: dict = {
		"blocking_reason_ids": [str(reason_id) for reason_id in reason_ids],
		"comment": comment,
		"field_reports": field_reports or [],
	}
	response = await client.post(
		f"/api/v1/tickets/{ticket_id}/block",
		headers=headers,
		json=body,
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


async def _field_reports_for_ticket(
	db_session: AsyncSession, ticket_id: uuid.UUID
) -> list[TicketFieldReport]:
	result = await db_session.execute(
		select(TicketFieldReport)
		.where(TicketFieldReport.ticket_id == ticket_id)
		.order_by(TicketFieldReport.created_at)
	)
	return list(result.scalars().all())


async def test_soft_block_transitions_to_blocked_with_field_reports(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	soft_block_reason: BlockingReason,
) -> None:
	sku_id = _sku_id_from_ticket(in_review_ticket)
	field_reports = [
		{
			"field_path": "description",
			"message": "Description copied from another product",
		},
		{
			"field_path": "sku_price",
			"message": "Price is suspiciously low for this brand",
			"sku_id": str(sku_id),
		},
		{
			"field_path": "product_images",
			"message": "Low quality photos, product is not visible",
		},
	]
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _block(
		client,
		in_review_ticket.id,
		[soft_block_reason.id],
		headers,
		field_reports=field_reports,
	)
	assert status_code == 200

	await db_session.refresh(in_review_ticket)
	assert in_review_ticket.status == TicketStatus.BLOCKED
	assert in_review_ticket.decision_at is not None
	assert in_review_ticket.blocking_reason_id == soft_block_reason.id
	assert in_review_ticket.moderator_comment == (
		"Description and photos do not match the product"
	)

	stored_reports = await _field_reports_for_ticket(db_session, in_review_ticket.id)
	assert len(stored_reports) == 3
	assert stored_reports[0].field_path == "description"
	assert stored_reports[1].field_path == "sku_price"
	assert stored_reports[1].sku_id == sku_id
	assert stored_reports[2].field_path == "product_images"


async def test_soft_block_emits_event_to_b2b(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	soft_block_reason: BlockingReason,
) -> None:
	sku_id = _sku_id_from_ticket(in_review_ticket)
	field_reports = [
		{
			"field_path": "description",
			"message": "Description copied from another product",
		},
		{
			"field_path": "sku_price",
			"message": "Price is suspiciously low",
			"sku_id": str(sku_id),
		},
	]
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _block(
		client,
		in_review_ticket.id,
		[soft_block_reason.id],
		headers,
		field_reports=field_reports,
	)
	assert status_code == 200

	outbox = await _latest_outbox_event(db_session, ticket_fixture_data.product_id)
	assert outbox is not None
	assert outbox.routing_key == "b2b.moderation.result"
	assert outbox.payload["event_type"] == "BLOCKED"
	assert outbox.payload["hard_block"] is False
	assert outbox.payload["blocking_reason_id"] == str(soft_block_reason.id)
	assert outbox.payload["product_id"] == str(ticket_fixture_data.product_id)
	assert outbox.payload["moderator_id"] == str(ticket_fixture_data.moderator_id)

	event_reports = outbox.payload["field_reports"]
	assert len(event_reports) == 2
	assert event_reports[0]["field_name"] == "description"
	assert event_reports[0]["comment"] == "Description copied from another product"
	assert event_reports[1]["field_name"] == "sku_price"
	assert event_reports[1]["sku_id"] == str(sku_id)


async def test_soft_block_unknown_reason_returns_400(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
) -> None:
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _block(
		client,
		in_review_ticket.id,
		[uuid.uuid4()],
		headers,
	)
	assert status_code == 400


async def test_soft_block_others_card_returns_403(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	soft_block_reason: BlockingReason,
	other_moderator: Moderator,
) -> None:
	headers = await auth_headers(other_moderator.id, db_session)

	status_code = await _block(
		client,
		in_review_ticket.id,
		[soft_block_reason.id],
		headers,
	)
	assert status_code == 403


async def test_soft_block_invalid_field_name_returns_400(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	ticket_fixture_data: TicketFixtureData,
	soft_block_reason: BlockingReason,
) -> None:
	headers = await auth_headers(ticket_fixture_data.moderator_id, db_session)

	status_code = await _block(
		client,
		in_review_ticket.id,
		[soft_block_reason.id],
		headers,
		field_reports=[
			{
				"field_path": "invalid_field",
				"message": "This field is not supported",
			}
		],
	)
	assert status_code == 400


async def test_soft_block_hard_only_reason_routes_to_hard_block(
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

	outbox = await _latest_outbox_event(db_session, ticket_fixture_data.product_id)
	assert outbox is not None
	assert outbox.payload["hard_block"] is True
