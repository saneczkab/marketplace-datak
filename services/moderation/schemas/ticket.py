from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from core.config import settings
from database.models.tickets.ticket import Ticket, TicketKind, TicketStatus

ALLOWED_FIELD_REPORT_PATHS: frozenset[str] = frozenset(
	{
		"title",
		"description",
		"product_images",
		"category",
		"sku_name",
		"sku_image",
		"sku_price",
	}
)


class ApproveTicketRequest(BaseModel):
	comment: str | None = Field(default=None, max_length=2000)


class ClaimTicketRequest(BaseModel):
	queue_priority: int | None = Field(default=None, ge=1, le=4)
	category_ids: list[UUID] | None = None


class FieldReportSeverity(str, Enum):
	INFO = "INFO"
	WARNING = "WARNING"
	ERROR = "ERROR"


class BlockFieldReport(BaseModel):
	field_path: str
	message: str = Field(max_length=1000)
	severity: FieldReportSeverity = FieldReportSeverity.ERROR
	sku_id: UUID | None = None


class BlockDecisionRequest(BaseModel):
	blocking_reason_ids: list[UUID] = Field(min_length=1)
	comment: str | None = Field(default=None, max_length=2000)
	field_reports: list[BlockFieldReport] = Field(default_factory=list)


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
		claim_expires_at = None
		if ticket.claimed_at is not None:
			claim_expires_at = ticket.claimed_at + timedelta(
				minutes=settings.IN_REVIEW_CLAIM_TIMEOUT_MINUTES
			)
		return cls(
			id=ticket.id,
			product_id=ticket.product_id,
			seller_id=ticket.seller_id,
			category_id=ticket.category_id,
			kind=ticket.kind,
			status=ticket.status,
			queue_priority=ticket.queue_priority,
			assigned_moderator_id=ticket.assigned_moderator_id,
			claimed_at=ticket.claimed_at,
			claim_expires_at=claim_expires_at,
			decision_at=ticket.decision_at,
			created_at=ticket.created_at,
			updated_at=ticket.updated_at,
		)
