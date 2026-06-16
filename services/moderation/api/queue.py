from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.ticket import ModeratorAlreadyHasTicketInReviewError
from schemas.ticket import ClaimTicketRequest, TicketResponse
from services import queue_service

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.post(
	"/claim",
	response_model=TicketResponse,
)
async def claim_next_ticket_endpoint(
	request: Request,
	db: Annotated[AsyncSession, Depends(get_db)],
	body: ClaimTicketRequest | None = None,
) -> TicketResponse | Response:
	moderator_id = request.state.user_id
	try:
		ticket = await queue_service.claim_next_ticket_response(db, moderator_id, body)
	except ModeratorAlreadyHasTicketInReviewError as exc:
		raise HTTPException(
			status_code=409,
			detail={"code": "CONFLICT", "message": str(exc)},
		) from exc

	if ticket is None:
		return Response(status_code=204)

	return ticket
