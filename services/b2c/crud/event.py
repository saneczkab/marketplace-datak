from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from database.models import B2BEvent


async def get_event_by_idempotency_key(
	idempotency_key: UUID, db: AsyncSession
) -> B2BEvent | None:
	result = await db.execute(
		select(B2BEvent).where(B2BEvent.idempotency_key == idempotency_key)
	)
	return result.scalar_one_or_none()


async def add_event(event: B2BEvent, db: AsyncSession) -> B2BEvent:
	db.add(event)
	await db.commit()
	await db.refresh(event)

	return event
