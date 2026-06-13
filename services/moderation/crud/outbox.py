from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import SessionLocal
from database.models.outbox import OutboxEvent, OutboxEventStatus
from schemas.moderation_event import ModerationEventRequest

PublishFn = Callable[[str, dict], Awaitable[None]]

MODERATION_RESULT_ROUTING_KEY = "b2b.moderation.result"
MODERATION_RESULT_EVENT_TYPE = "b2b.moderation.result"


def build_moderation_result_payload(request: ModerationEventRequest) -> dict:
	return request.model_dump(mode="json")


async def enqueue_moderation_result(
	db: AsyncSession,
	request: ModerationEventRequest,
) -> OutboxEvent:
	payload = build_moderation_result_payload(request)
	outbox_event = OutboxEvent(
		idempotency_key=request.idempotency_key,
		event_type=MODERATION_RESULT_EVENT_TYPE,
		routing_key=MODERATION_RESULT_ROUTING_KEY,
		payload=payload,
		status=OutboxEventStatus.PENDING,
	)
	db.add(outbox_event)
	await db.flush()
	return outbox_event


async def fetch_pending_events(db: AsyncSession, limit: int = 50) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent)
		.where(OutboxEvent.status == OutboxEventStatus.PENDING)
		.order_by(OutboxEvent.created_at)
		.limit(limit)
	)
	return list(result.scalars().all())


async def get_pending_event_by_id(
	db: AsyncSession, event_id: UUID
) -> OutboxEvent | None:
	event = await db.get(OutboxEvent, event_id)
	if event is None or event.status != OutboxEventStatus.PENDING:
		return None
	return event


async def mark_event_sent(db: AsyncSession, event: OutboxEvent) -> None:
	event.status = OutboxEventStatus.SENT
	event.sent_at = datetime.now(timezone.utc)
	db.add(event)
	await db.commit()


async def deliver_pending_event(
	db: AsyncSession,
	event_id: UUID,
	publish: PublishFn,
) -> bool:
	db_event = await get_pending_event_by_id(db, event_id)
	if db_event is None:
		return False
	try:
		await publish(db_event.routing_key, db_event.payload)
		await mark_event_sent(db, db_event)
		return True
	except Exception:  # noqa: BLE001
		await db.rollback()
		return False


async def process_pending_batch(publish: PublishFn, limit: int = 50) -> int:
	processed = 0
	async with SessionLocal() as db:
		events = await fetch_pending_events(db, limit=limit)

	for event in events:
		async with SessionLocal() as db:
			if await deliver_pending_event(db, event.id, publish):
				processed += 1
	return processed
