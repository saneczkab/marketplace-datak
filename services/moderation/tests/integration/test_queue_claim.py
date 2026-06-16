import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity.moderator import Moderator
from database.models.tickets.ticket import Ticket, TicketStatus
from tests.integration.conftest import (
	auth_headers,
	persist_moderator,
	persist_ticket,
	sample_product_snapshot,
	seed_catalog_replica,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _claim(
	client: AsyncClient,
	headers: dict[str, str],
	body: dict | None = None,
) -> tuple[int, dict | None]:
	response = await client.post(
		"/api/v1/queue/claim",
		headers=headers,
		json=body,
	)
	if response.status_code == 204:
		return response.status_code, None
	if response.content:
		return response.status_code, response.json()
	return response.status_code, None


async def _persist_pending_ticket(
	db_session: AsyncSession,
	product_id: uuid.UUID,
	seller_id: uuid.UUID,
	*,
	queue_priority: int = 1,
	created_at: datetime | None = None,
) -> Ticket:
	await seed_catalog_replica(db_session, product_id, seller_id)
	ticket = await persist_ticket(
		db_session,
		product_id=product_id,
		seller_id=seller_id,
		status=TicketStatus.PENDING,
		queue_priority=queue_priority,
		json_after=sample_product_snapshot(product_id, seller_id),
	)
	if created_at is not None:
		await db_session.execute(
			update(Ticket).where(Ticket.id == ticket.id).values(created_at=created_at)
		)
		await db_session.commit()
		await db_session.refresh(ticket)
	return ticket


async def test_next_returns_oldest_pending(
	client: AsyncClient,
	db_session: AsyncSession,
	moderator: Moderator,
) -> None:
	seller_id = uuid.uuid4()
	older_product_id = uuid.uuid4()
	newer_product_id = uuid.uuid4()
	base_time = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)

	older_ticket = await _persist_pending_ticket(
		db_session,
		older_product_id,
		seller_id,
		created_at=base_time,
	)
	await _persist_pending_ticket(
		db_session,
		newer_product_id,
		seller_id,
		created_at=base_time + timedelta(hours=1),
	)

	headers = await auth_headers(moderator.id, db_session)
	status_code, body = await _claim(client, headers)

	assert status_code == 200
	assert body is not None
	assert body["id"] == str(older_ticket.id)
	assert body["status"] == TicketStatus.IN_REVIEW.value
	assert body["assigned_moderator_id"] == str(moderator.id)
	assert body["claimed_at"] is not None
	assert body["claim_expires_at"] is not None

	await db_session.refresh(older_ticket)
	assert older_ticket.status == TicketStatus.IN_REVIEW
	assert older_ticket.assigned_moderator_id == moderator.id
	assert older_ticket.claimed_at is not None


async def test_concurrent_two_moderators_get_different_cards(
	client: AsyncClient,
	db_session: AsyncSession,
) -> None:
	seller_id = uuid.uuid4()
	moderator_a = await persist_moderator(db_session)
	moderator_b = await persist_moderator(db_session)
	base_time = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)

	await _persist_pending_ticket(
		db_session,
		uuid.uuid4(),
		seller_id,
		created_at=base_time,
	)
	await _persist_pending_ticket(
		db_session,
		uuid.uuid4(),
		seller_id,
		created_at=base_time + timedelta(minutes=1),
	)

	headers_a = await auth_headers(moderator_a.id, db_session)
	headers_b = await auth_headers(moderator_b.id, db_session)

	results = await asyncio.gather(
		_claim(client, headers_a),
		_claim(client, headers_b),
	)

	assert all(status == 200 for status, _ in results)
	ticket_ids = {body["id"] for _, body in results if body is not None}
	assert len(ticket_ids) == 2


async def test_empty_queue_returns_204(
	client: AsyncClient,
	db_session: AsyncSession,
	moderator: Moderator,
) -> None:
	await db_session.execute(delete(Ticket))
	await db_session.commit()

	headers = await auth_headers(moderator.id, db_session)
	status_code, body = await _claim(client, headers)

	assert status_code == 204
	assert body is None


async def test_moderator_already_has_in_review_returns_409(
	client: AsyncClient,
	db_session: AsyncSession,
	in_review_ticket: Ticket,
	moderator: Moderator,
) -> None:
	_ = in_review_ticket
	seller_id = uuid.uuid4()
	await _persist_pending_ticket(db_session, uuid.uuid4(), seller_id)

	headers = await auth_headers(moderator.id, db_session)
	status_code, body = await _claim(client, headers)

	assert status_code == 409
	assert body is not None
	assert body["code"] == "CONFLICT"
