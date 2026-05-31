from fastapi import APIRouter, Header

from typing import Annotated

from schemas.event import B2BEvent


router = APIRouter(prefix="/api/v1")


@router.post("/b2b/events", status_code=202)
async def product_event(
	X_Service_Key: Annotated[str, Header()], event: B2BEvent
) -> None:
	pass
