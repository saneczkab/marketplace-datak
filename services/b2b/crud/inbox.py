from database.models import InboxEvent, InboxEventStatusEnum

from typing import Awaitable, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

ProcessFN = Callable[[str, dict], Awaitable[None]]


async def get_all_pending_events(db: AsyncSession, limit: int = 50) -> list[InboxEvent]:
	result = await db.execute(
		select(InboxEvent)
		.where(InboxEvent.status == InboxEventStatusEnum.PENDING)
		.order_by(InboxEvent.created_at)
		.limit(limit)
	)

	return list(result.scalars().all())


async def mark_event_processed(event: InboxEvent, db: AsyncSession) -> None:
	event.status = InboxEventStatusEnum.PROCESSED
	event.processed_at = datetime.now(timezone.utc)

	db.add(event)
	await db.commit()


async def mark_event_failed(event: InboxEvent, db: AsyncSession) -> None:
	event.status = InboxEventStatusEnum.FAILED
	event.processed_at = datetime.now(timezone.utc)

	db.add(event)
	await db.commit()


async def process_inbox_event(
	db: AsyncSession,
	event_id: uuid.UUID,
	handler: ProcessFN,
) -> bool:
	event = await db.get(InboxEvent, event_id)
	if not event or event.status != InboxEventStatusEnum.PENDING:
		return False

	try:
		await handler(event.routing_key, event.payload)
		await mark_event_processed(event_id, db)
		return True
	except Exception as e:  # noqa
		await db.rollback()
		await mark_event_failed(event, db)
		return False


async def process_pending_inbox_batch(
	handler: ProcessFN, db: AsyncSession, limit: int = 50
) -> int:
	processed = 0
	events = await get_all_pending_events(db, limit=limit)

	for event in events:
		if await process_inbox_event(db, event.id, handler):
			processed += 1

	return processed
