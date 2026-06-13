from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.ticket import (
	TicketHardBlockedError,
	TicketNoSkusError,
	TicketNotAssignedError,
	TicketNotFoundError,
	TicketWrongStatusError,
)
from schemas.ticket import ApproveTicketRequest, TicketResponse
from services import ticket_decision_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def _current_moderator_id(request: Request) -> UUID:
	return UUID(request.state.user_id)


@router.post("/{ticket_id}/approve", response_model=TicketResponse)
async def approve_ticket_endpoint(
	ticket_id: UUID,
	request: Request,
	db: Annotated[AsyncSession, Depends(get_db)],
	body: ApproveTicketRequest | None = None,
) -> TicketResponse:
	moderator_id = _current_moderator_id(request)
	comment = body.comment if body is not None else None
	try:
		return await ticket_decision_service.approve_ticket(
			db, ticket_id, moderator_id, comment
		)
	except TicketNotFoundError as exc:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(exc)},
		) from exc
	except TicketNotAssignedError as exc:
		raise HTTPException(
			status_code=403,
			detail={"code": "FORBIDDEN", "message": str(exc)},
		) from exc
	except (
		TicketWrongStatusError,
		TicketNoSkusError,
		TicketHardBlockedError,
	) as exc:
		raise HTTPException(
			status_code=409,
			detail={"code": "CONFLICT", "message": str(exc)},
		) from exc
