from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.processed_events.catalog import ProcessedCatalogEvent

CATALOG_IDEMPOTENCY_TTL = timedelta(hours=24)
DEFAULT_SENDER_SERVICE = "b2b"


async def get_processed_event(
	db: AsyncSession, sender_service: str, idempotency_key: UUID
) -> ProcessedCatalogEvent | None:
	result = await db.execute(
		select(ProcessedCatalogEvent).where(
			ProcessedCatalogEvent.sender_service == sender_service,
			ProcessedCatalogEvent.idempotency_key == idempotency_key,
		)
	)
	return result.scalar_one_or_none()


async def delete_processed_event(
	db: AsyncSession, sender_service: str, idempotency_key: UUID
) -> None:
	await db.execute(
		delete(ProcessedCatalogEvent).where(
			ProcessedCatalogEvent.sender_service == sender_service,
			ProcessedCatalogEvent.idempotency_key == idempotency_key,
		)
	)
	await db.flush()


def processed_event_is_valid(
	event: ProcessedCatalogEvent, now: datetime | None = None
) -> bool:
	current = now or datetime.now(timezone.utc)
	processed_at = event.processed_at
	if processed_at.tzinfo is None:
		processed_at = processed_at.replace(tzinfo=timezone.utc)
	return current - processed_at < CATALOG_IDEMPOTENCY_TTL


async def record_processed_event(
	db: AsyncSession,
	sender_service: str,
	idempotency_key: UUID,
	event_type: str,
) -> None:
	db.add(
		ProcessedCatalogEvent(
			sender_service=sender_service,
			idempotency_key=idempotency_key,
			event_type=event_type,
		)
	)
	await db.flush()
