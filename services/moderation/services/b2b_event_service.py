import json

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from crud import b2b_event as b2b_event_crud
from exceptions.b2b_event import B2BEventValidationError
from schemas.b2b_event import IncomingB2BEvent


def parse_b2b_event(body: bytes) -> IncomingB2BEvent:
	try:
		raw = json.loads(body)
	except json.JSONDecodeError as exc:
		raise B2BEventValidationError(str(exc)) from exc
	try:
		return IncomingB2BEvent.model_validate(raw)
	except ValidationError as exc:
		raise B2BEventValidationError(str(exc)) from exc


async def receive_event(
	db: AsyncSession,
	event: IncomingB2BEvent,
	sender_service: str = b2b_event_crud.DEFAULT_SENDER_SERVICE,
) -> bool:
	return await b2b_event_crud.apply_b2b_event(
		db, event, sender_service=sender_service
	)
