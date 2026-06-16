import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.tickets.ticket import Ticket, TicketKind, TicketStatus
from tests.integration.conftest import (
	B2B_SERVICE_KEY_HEADERS,
	TicketFixtureData,
	persist_ticket,
	product_created_body,
	product_deleted_body,
	product_edited_body,
	sample_product_snapshot,
	seed_catalog_replica,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _get_ticket(db: AsyncSession, product_id: uuid.UUID) -> Ticket | None:
	result = await db.execute(
		select(Ticket)
		.where(Ticket.product_id == product_id)
		.execution_options(populate_existing=True)
	)
	return result.scalar_one_or_none()


async def test_created_pending(
	client: AsyncClient,
	db_session: AsyncSession,
	ticket_fixture_data: TicketFixtureData,
) -> None:
	product_id = uuid.uuid4()
	seller_id = ticket_fixture_data.seller_id
	await seed_catalog_replica(
		db_session, product_id, seller_id, title="Catalog product"
	)
	body = product_created_body(product_id, seller_id)

	response = await client.post(
		"/api/v1/b2b/events",
		headers=B2B_SERVICE_KEY_HEADERS,
		json=body,
	)
	assert response.status_code == 202

	ticket = await _get_ticket(db_session, product_id)
	assert ticket is not None
	assert ticket.status == TicketStatus.PENDING
	assert ticket.queue_priority == 1
	assert ticket.json_before is None
	assert ticket.json_after["title"] == "Catalog product"
	for sku in ticket.json_after.get("skus", []):
		assert "cost_price" not in sku
		assert "reserved_quantity" not in sku


async def test_edited_returns_to_review(
	client: AsyncClient,
	db_session: AsyncSession,
	ticket_fixture_data: TicketFixtureData,
) -> None:
	seller_id = ticket_fixture_data.seller_id

	for product_id, prior_status, expected_priority in (
		(uuid.uuid4(), TicketStatus.APPROVED, 3),
		(uuid.uuid4(), TicketStatus.BLOCKED, 2),
	):
		await seed_catalog_replica(db_session, product_id, seller_id)
		ticket = await persist_ticket(
			db_session,
			product_id=product_id,
			seller_id=seller_id,
			status=prior_status,
			kind=TicketKind.EDIT,
			queue_priority=expected_priority,
			json_after=sample_product_snapshot(product_id, seller_id),
		)
		old_json_after = ticket.json_after
		body = product_edited_body(product_id, seller_id)

		response = await client.post(
			"/api/v1/b2b/events",
			headers=B2B_SERVICE_KEY_HEADERS,
			json=body,
		)
		assert response.status_code == 202

		updated = await _get_ticket(db_session, product_id)
		assert updated is not None
		assert updated.status == TicketStatus.PENDING
		assert updated.assigned_moderator_id is None
		assert updated.queue_priority == expected_priority
		assert updated.json_before == old_json_after
		assert updated.json_after["title"] == "Test product"


async def test_edited_updates_in_review(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
) -> None:
	old_json_after = in_review_ticket.json_after
	await seed_catalog_replica(
		db_session,
		in_review_ticket.product_id,
		in_review_ticket.seller_id,
		title="Updated catalog product",
	)
	body = product_edited_body(
		in_review_ticket.product_id,
		in_review_ticket.seller_id,
	)

	response = await client.post(
		"/api/v1/b2b/events",
		headers=B2B_SERVICE_KEY_HEADERS,
		json=body,
	)
	assert response.status_code == 202

	updated = await _get_ticket(db_session, in_review_ticket.product_id)
	assert updated is not None
	assert updated.status == TicketStatus.PENDING
	assert updated.assigned_moderator_id is None
	assert updated.json_before == old_json_after
	assert updated.json_after["title"] == "Updated catalog product"


async def test_deleted_archived(
	client: AsyncClient,
	db_session: AsyncSession,
	pending_ticket: Ticket,
) -> None:
	body = product_deleted_body(pending_ticket.product_id)

	response = await client.post(
		"/api/v1/b2b/events",
		headers=B2B_SERVICE_KEY_HEADERS,
		json=body,
	)
	assert response.status_code == 202

	ticket = await _get_ticket(db_session, pending_ticket.product_id)
	assert ticket is None


async def test_duplicate_event_no_side_effects(
	client: AsyncClient,
	db_session: AsyncSession,
	ticket_fixture_data: TicketFixtureData,
) -> None:
	product_id = uuid.uuid4()
	seller_id = ticket_fixture_data.seller_id
	await seed_catalog_replica(db_session, product_id, seller_id)
	idempotency_key = uuid.uuid4()
	body = product_created_body(product_id, seller_id, idempotency_key=idempotency_key)

	first = await client.post(
		"/api/v1/b2b/events",
		headers=B2B_SERVICE_KEY_HEADERS,
		json=body,
	)
	assert first.status_code == 202

	after_first = await _get_ticket(db_session, product_id)

	second = await client.post(
		"/api/v1/b2b/events",
		headers=B2B_SERVICE_KEY_HEADERS,
		json=body,
	)
	assert second.status_code == 202

	after_second = await _get_ticket(db_session, product_id)
	assert after_second is not None
	assert after_second.status == after_first.status
	assert after_second.queue_priority == after_first.queue_priority
	assert after_second.json_after == after_first.json_after
	assert after_second.updated_at == after_first.updated_at


async def test_missing_service_header_401(
	client: AsyncClient,
	ticket_fixture_data: TicketFixtureData,
) -> None:
	body = product_created_body(uuid.uuid4(), ticket_fixture_data.seller_id)

	response = await client.post("/api/v1/b2b/events", json=body)
	assert response.status_code == 401
	assert response.json()["code"] == "UNAUTHORIZED"
