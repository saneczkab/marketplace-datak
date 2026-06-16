from database.models import InboxEvent

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid


async def get_event_by_idempotency_eky(
	idempotency_key: uuid.UUID, db: AsyncSession
) -> InboxEvent | None:
	return (
		await db.execute(
			select(InboxEvent).where(InboxEvent.idempotency_key == idempotency_key)
		)
	).scalar_one_or_none()


async def add_event(event: InboxEvent, db: AsyncSession) -> InboxEvent:
	db.add(event)
	await db.commit()
	await db.refresh(event)

	return event
