from sqlalchemy.ext.asyncio import AsyncSession

from crud import moderation_event as moderation_event_crud
from exceptions.moderation_event import ModerationEventValidationError
from exceptions.product import ProductNotFoundError
from pydantic import ValidationError
from schemas.moderation_event import ModerationEventRequest


async def receive_moderation_event(
	db: AsyncSession,
	request: ModerationEventRequest,
	sender_service: str = moderation_event_crud.DEFAULT_SENDER_SERVICE,
) -> None:
	try:
		await moderation_event_crud.apply_moderation_event(
			db, request, sender_service=sender_service
		)
	except ProductNotFoundError as exc:
		raise exc
	except ValidationError as exc:
		raise ModerationEventValidationError(str(exc)) from exc


async def receive_moderation_event_payload(
	db: AsyncSession,
	payload: dict,
	sender_service: str = moderation_event_crud.DEFAULT_SENDER_SERVICE,
) -> None:
	try:
		request = ModerationEventRequest.model_validate(payload)
	except ValidationError as exc:
		raise ModerationEventValidationError(str(exc)) from exc
	await receive_moderation_event(db, request, sender_service=sender_service)
