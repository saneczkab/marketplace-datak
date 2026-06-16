from database.models import InboxEvent

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from database.models.event.inbox import InboxEventStatusEnum


async def get_event_by_idempotency_key(
	idempotency_key: uuid.UUID, db: AsyncSession
) -> InboxEvent | None:
	return (
		await db.execute(
			select(InboxEvent).where(InboxEvent.idempotency_key == idempotency_key)
		)
	).scalar_one_or_none()


async def add_event(event: InboxEvent, db: AsyncSession) -> None:
	db.add(event)
	await db.commit()


async def get_all_pending_events(db: AsyncSession, limit: int = 50) -> list[InboxEvent]:
	result = await db.execute(
		select(InboxEvent)
		.where(InboxEvent.status == InboxEventStatusEnum.PENDING)
		.order_by(InboxEvent.created_at)
		.limit(limit)
	)
	return list(result.scalars().all())


async def mark_event_proccessed(event_id: uuid.UUID, db: AsyncSession) -> None:
	event = (
		await db.execute(select(InboxEvent).where(InboxEvent.id == event_id))
	).scalar_one_or_none()

	if not event:
		return

	event.status = "PROCESSED"
	event.processed_at = datetime.now(timezone.utc)
	await db.commit()


async def mark_event_failed(event_id: uuid.UUID, db: AsyncSession) -> None:
	event = (
		await db.execute(select(InboxEvent).where(InboxEvent.id == event_id))
	).scalar_one_or_none()

	if not event:
		return

	event.status = "FAILED"
	await db.commit()
