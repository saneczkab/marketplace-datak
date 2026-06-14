from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import queue as queue_crud
from database.models.tickets.ticket import Ticket
from schemas.ticket import ClaimTicketRequest, TicketResponse


async def claim_next_ticket(
	db: AsyncSession,
	moderator_id: UUID,
	body: ClaimTicketRequest | None = None,
) -> Ticket | None:
	queue_priority = body.queue_priority if body is not None else None
	category_ids = body.category_ids if body is not None else None
	ticket = await queue_crud.claim_next_ticket(
		db,
		moderator_id,
		queue_priority=queue_priority,
		category_ids=category_ids,
	)
	return ticket


async def claim_next_ticket_response(
	db: AsyncSession,
	moderator_id: UUID,
	body: ClaimTicketRequest | None = None,
) -> TicketResponse | None:
	ticket = await claim_next_ticket(db, moderator_id, body)
	if ticket is None:
		return None
	return TicketResponse.from_ticket(ticket)
