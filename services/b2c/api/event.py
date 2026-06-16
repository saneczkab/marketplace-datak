from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated
import logging

from exceptions.event import EventDuplicatError
from schemas.event import B2BEvent

from services import event_service
from core.db import get_db

logger = logging.getLogger("api.events")

router = APIRouter(prefix="/api/v1/b2b", tags=["events"])


@router.post("/events", status_code=202)
async def product_event(
	event: B2BEvent,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
	try:
		await event_service.handle_b2b_event(event, db)
	except EventDuplicatError as e:
		raise HTTPException(
			status_code=409, detail="idempotency key already handled"
		) from e
	except Exception as e:
		logger.error(f"Error: {e}")
		raise HTTPException(status_code=418, detail=f"{e}") from e
