from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated

from schemas.event import B2BEvent

from services import event_service
from core.db import get_db

router = APIRouter(prefix="/api/v1/b2b", tags=["events"])


@router.post("/events", status_code=202)
async def product_event(
	event: B2BEvent,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
	try:
		await event_service.handle_b2b_event(event, db)
	except Exception as e:
		raise HTTPException(status_code=418, detail=f"{e}") from e
