from sqlalchemy.ext.asyncio import AsyncSession

from crud import catalog as catalog_crud
from crud import processed_catalog_event as processed_catalog_event_crud
from exceptions.catalog import CatalogEventValidationError
from schemas.catalog_event import (
	IncomingCatalogEvent,
	ProductUpdatePayload,
	SkuUpdatePayload,
)

DEFAULT_SENDER_SERVICE = processed_catalog_event_crud.DEFAULT_SENDER_SERVICE


async def apply_catalog_event(
	db: AsyncSession,
	event: IncomingCatalogEvent,
	sender_service: str = DEFAULT_SENDER_SERVICE,
) -> bool:
	existing = await processed_catalog_event_crud.get_processed_event(
		db, sender_service, event.idempotency_key
	)
	if existing is not None:
		if processed_catalog_event_crud.processed_event_is_valid(existing):
			return False
		await processed_catalog_event_crud.delete_processed_event(
			db, sender_service, event.idempotency_key
		)

	if isinstance(event.payload, ProductUpdatePayload):
		await catalog_crud.upsert_product(db, event.payload)
	elif isinstance(event.payload, SkuUpdatePayload):
		try:
			await catalog_crud.upsert_sku(db, event.payload)
		except ValueError as exc:
			raise CatalogEventValidationError(str(exc)) from exc
	else:
		raise CatalogEventValidationError("Unsupported catalog event payload")

	await processed_catalog_event_crud.record_processed_event(
		db,
		sender_service=sender_service,
		idempotency_key=event.idempotency_key,
		event_type=event.event_type.value,
	)
	await db.commit()
	return True
