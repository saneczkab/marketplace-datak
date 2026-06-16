import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.blocking_reason import BlockingReason
from database.models.identity.moderator import Moderator
from database.models.tickets.ticket import Ticket, TicketStatus
from tests.integration.conftest import (
	TicketFixtureData,
	auth_headers,
	persist_ticket,
	sample_product_snapshot,
	seed_catalog_replica,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

BLOCKING_REASONS_URL = "/api/v1/blocking-reasons"


async def test_list_returns_active_reasons(
	client: AsyncClient,
	db_session: AsyncSession,
	moderator: Moderator,
	active_soft_blocking_reason: BlockingReason,
	active_hard_blocking_reason: BlockingReason,
	inactive_blocking_reason: BlockingReason,
) -> None:
	_ = inactive_blocking_reason

	headers = await auth_headers(moderator.id, db_session)
	response = await client.get(BLOCKING_REASONS_URL, headers=headers)

	assert response.status_code == 200
	payload = response.json()
	returned_ids = {item["id"] for item in payload}
	assert str(active_soft_blocking_reason.id) in returned_ids
	assert str(active_hard_blocking_reason.id) in returned_ids
	assert all(item["is_active"] is True for item in payload)

	for item in payload:
		if item["id"] == str(active_soft_blocking_reason.id):
			assert item["title"] == "Active soft reason"
			assert item["hard_block"] is False
			assert item["code"] == "ACTIVE_SOFT"
		if item["id"] == str(active_hard_blocking_reason.id):
			assert item["title"] == "Active hard reason"
			assert item["hard_block"] is True


async def test_inactive_reasons_not_visible(
	client: AsyncClient,
	db_session: AsyncSession,
	moderator: Moderator,
	visible_blocking_reason: BlockingReason,
	hidden_blocking_reason: BlockingReason,
) -> None:
	headers = await auth_headers(moderator.id, db_session)
	response = await client.get(BLOCKING_REASONS_URL, headers=headers)

	assert response.status_code == 200
	returned_ids = {item["id"] for item in response.json()}
	assert str(visible_blocking_reason.id) in returned_ids
	assert str(hidden_blocking_reason.id) not in returned_ids

	inactive_response = await client.get(
		f"{BLOCKING_REASONS_URL}?is_active=false",
		headers=headers,
	)
	assert inactive_response.status_code == 200
	inactive_ids = {item["id"] for item in inactive_response.json()}
	assert str(hidden_blocking_reason.id) in inactive_ids
	assert str(visible_blocking_reason.id) not in inactive_ids


async def test_list_filters_by_hard_block(
	client: AsyncClient,
	db_session: AsyncSession,
	moderator: Moderator,
	soft_block_reason: BlockingReason,
	hard_block_reason: BlockingReason,
) -> None:
	headers = await auth_headers(moderator.id, db_session)

	soft_response = await client.get(
		f"{BLOCKING_REASONS_URL}?hard_block=false",
		headers=headers,
	)
	assert soft_response.status_code == 200
	soft_ids = {item["id"] for item in soft_response.json()}
	assert str(soft_block_reason.id) in soft_ids
	assert str(hard_block_reason.id) not in soft_ids

	hard_response = await client.get(
		f"{BLOCKING_REASONS_URL}?hard_block=true",
		headers=headers,
	)
	assert hard_response.status_code == 200
	hard_ids = {item["id"] for item in hard_response.json()}
	assert str(hard_block_reason.id) in hard_ids
	assert str(soft_block_reason.id) not in hard_ids


async def test_referenced_reason_cannot_be_deleted(
	client: AsyncClient,
	db_session: AsyncSession,
	ticket_fixture_data: TicketFixtureData,
	moderator: Moderator,
	referenced_blocking_reason: BlockingReason,
) -> None:
	_ = moderator
	reason_id = referenced_blocking_reason.id
	await seed_catalog_replica(
		db_session,
		ticket_fixture_data.product_id,
		ticket_fixture_data.seller_id,
	)
	await persist_ticket(
		db_session,
		product_id=ticket_fixture_data.product_id,
		seller_id=ticket_fixture_data.seller_id,
		status=TicketStatus.BLOCKED,
		blocking_reason_id=reason_id,
		json_after=sample_product_snapshot(
			ticket_fixture_data.product_id,
			ticket_fixture_data.seller_id,
		),
	)

	moderator_id = ticket_fixture_data.moderator_id

	with pytest.raises(IntegrityError):
		await db_session.delete(referenced_blocking_reason)
		await db_session.commit()

	await db_session.rollback()

	headers = await auth_headers(moderator_id, db_session)
	response = await client.delete(
		f"{BLOCKING_REASONS_URL}/{reason_id}",
		headers=headers,
	)
	assert response.status_code == 204

	result = await db_session.execute(
		select(BlockingReason).where(BlockingReason.id == reason_id)
	)
	stored_reason = result.scalar_one()
	assert stored_reason.is_active is False

	ticket_result = await db_session.execute(
		select(Ticket).where(Ticket.product_id == ticket_fixture_data.product_id)
	)
	ticket = ticket_result.scalar_one()
	assert ticket.blocking_reason_id == reason_id


async def test_moderator_can_create_blocking_reason(
	client: AsyncClient,
	db_session: AsyncSession,
	moderator: Moderator,
) -> None:
	headers = await auth_headers(moderator.id, db_session)
	response = await client.post(
		BLOCKING_REASONS_URL,
		headers=headers,
		json={
			"code": "NEW_REASON",
			"title": "New reason",
			"description": "Details",
			"hard_block": False,
		},
	)

	assert response.status_code == 201
	payload = response.json()
	assert payload["code"] == "NEW_REASON"
	assert payload["title"] == "New reason"
	assert payload["is_active"] is True


async def test_create_duplicate_code_returns_conflict(
	client: AsyncClient,
	db_session: AsyncSession,
	moderator: Moderator,
	duplicate_code_blocking_reason: BlockingReason,
) -> None:
	_ = duplicate_code_blocking_reason
	headers = await auth_headers(moderator.id, db_session)
	response = await client.post(
		BLOCKING_REASONS_URL,
		headers=headers,
		json={
			"code": "DUPLICATE_CODE",
			"title": "Another",
			"hard_block": False,
		},
	)

	assert response.status_code == 409
	assert response.json()["code"] == "CONFLICT"
