from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.b2b_event import (
	B2BEventValidationError,
	TicketAlreadyExistsError,
	TicketNotFoundError,
)
from schemas.b2b_event import IncomingB2BEvent
from services import b2b_event_service

router = APIRouter(prefix="/b2b", tags=["B2B Events"])


@router.post("/events", status_code=202)
async def receive_b2b_event_endpoint(
	request: IncomingB2BEvent,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
	try:
		await b2b_event_service.receive_event(db, request)
	except (
		TicketNotFoundError,
		B2BEventValidationError,
		ValidationError,
		TicketAlreadyExistsError,
	) as exc:
		raise HTTPException(
			status_code=400,
			detail={"code": "VALIDATION_ERROR", "message": str(exc)},
		) from exc
