import json

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from crud import catalog_event as catalog_event_crud
from exceptions.catalog import CatalogEventValidationError
from schemas.catalog_event import IncomingCatalogEvent


def parse_catalog_event(body: bytes) -> IncomingCatalogEvent:
	try:
		raw = json.loads(body)
	except json.JSONDecodeError as exc:
		raise CatalogEventValidationError(str(exc)) from exc
	try:
		return IncomingCatalogEvent.model_validate(raw)
	except ValidationError as exc:
		raise CatalogEventValidationError(str(exc)) from exc


async def receive_event(
	db: AsyncSession,
	event: IncomingCatalogEvent,
	sender_service: str = catalog_event_crud.DEFAULT_SENDER_SERVICE,
) -> bool:
	return await catalog_event_crud.apply_catalog_event(
		db, event, sender_service=sender_service
	)


async def receive_message(
	db: AsyncSession,
	body: bytes,
	sender_service: str = catalog_event_crud.DEFAULT_SENDER_SERVICE,
) -> bool:
	event = parse_catalog_event(body)
	return await receive_event(db, event, sender_service=sender_service)
