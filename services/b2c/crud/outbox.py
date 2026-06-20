from database.models import OutboxEvent
from schemas.event import Event

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone


async def post_event(event: Event, db: AsyncSession) -> None:
	db_event = OutboxEvent(
		idempotency_key=event.idempotency_key,
		event_type=event.event_type,
		payload=event.payload.model_dump_json(),
		occurred_at=event.occurred_at,
	)

	db.add(db_event)
	await db.commit()


async def get_unsent_events(db: AsyncSession, limit: int = 50) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent).where(OutboxEvent.status == "PENDING").limit(limit)
	)

	return result.scalars().all()


async def mark_event_sent(event: OutboxEvent, db: AsyncSession) -> None:
	event.status = "SENT"
	event.sent_at = datetime.now(timezone.utc)
	db.add(event)
	await db.commit()
