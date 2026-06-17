from database.models import OutboxEvent
from schemas.event import Event

from sqlalchemy.ext.asyncio import AsyncSession


async def post_event(event: Event, db: AsyncSession) -> None:
	db_event = OutboxEvent(
		idempotency_key=event.idempotency_key,
		event_type=event.event_type,
		payload=event.payload.model_dump_json(),
		occured_at=event.occured_at,
	)

	db.add(db_event)
	await db.commit()
