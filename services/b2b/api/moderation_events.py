from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from crud.moderation_event import DEFAULT_SENDER_SERVICE
from exceptions.moderation_event import ModerationEventValidationError
from exceptions.product import ProductNotFoundError
from schemas.moderation_event import ModerationEventRequest
from services import moderation_event_service

router = APIRouter(prefix="/moderation", tags=["Moderation Events"])


@router.post("/events", status_code=204)
async def receive_moderation_event_endpoint(
	request: ModerationEventRequest,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
	try:
		await moderation_event_service.receive_moderation_event(
			db, request, sender_service=DEFAULT_SENDER_SERVICE
		)
	except ProductNotFoundError as exc:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(exc)},
		) from exc
	except (ModerationEventValidationError, ValidationError) as exc:
		raise HTTPException(
			status_code=400,
			detail={"code": "VALIDATION_ERROR", "message": str(exc)},
		) from exc
	return Response(status_code=204)
