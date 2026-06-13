from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import ticket_decision as ticket_decision_crud
from schemas.ticket import TicketResponse


async def approve_ticket(
	db: AsyncSession,
	ticket_id: UUID,
	moderator_id: UUID,
	comment: str | None,
) -> TicketResponse:
	ticket = await ticket_decision_crud.approve_ticket(
		db, ticket_id, moderator_id, comment
	)
	return TicketResponse.from_ticket(ticket)
