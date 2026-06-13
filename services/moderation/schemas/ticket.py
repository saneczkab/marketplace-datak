from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from database.models.tickets.ticket import Ticket, TicketKind, TicketStatus


class ApproveTicketRequest(BaseModel):
	comment: str | None = Field(default=None, max_length=2000)


class TicketResponse(BaseModel):
	id: UUID
	product_id: UUID
	seller_id: UUID
	category_id: UUID | None
	kind: TicketKind
	status: TicketStatus
	queue_priority: int
	assigned_moderator_id: UUID | None
	claimed_at: datetime | None = None
	claim_expires_at: datetime | None = None
	decision_at: datetime | None
	created_at: datetime
	updated_at: datetime

	@classmethod
	def from_ticket(cls, ticket: Ticket) -> "TicketResponse":
		return cls(
			id=ticket.id,
			product_id=ticket.product_id,
			seller_id=ticket.seller_id,
			category_id=ticket.category_id,
			kind=ticket.kind,
			status=ticket.status,
			queue_priority=ticket.queue_priority,
			assigned_moderator_id=ticket.assigned_moderator_id,
			decision_at=ticket.decision_at,
			created_at=ticket.created_at,
			updated_at=ticket.updated_at,
		)
