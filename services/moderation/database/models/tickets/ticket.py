import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.core import Base

if TYPE_CHECKING:
	from database.models.tickets.field_report import TicketFieldReport


class TicketStatus(str, enum.Enum):
	PENDING = "PENDING"
	IN_REVIEW = "IN_REVIEW"
	APPROVED = "APPROVED"
	BLOCKED = "BLOCKED"
	HARD_BLOCKED = "HARD_BLOCKED"


class TicketKind(str, enum.Enum):
	CREATE = "CREATE"
	EDIT = "EDIT"


class Ticket(Base):
	__tablename__ = "tickets"

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
	)
	product_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), unique=True, nullable=False
	)
	seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
	category_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID(as_uuid=True), nullable=True
	)
	kind: Mapped[TicketKind] = mapped_column(
		Enum(TicketKind, name="ticket_kind", native_enum=False),
		nullable=False,
	)
	status: Mapped[TicketStatus] = mapped_column(
		Enum(TicketStatus, name="ticket_status", native_enum=False),
		nullable=False,
	)
	queue_priority: Mapped[int] = mapped_column(Integer, nullable=False)
	total_active_quantity: Mapped[int] = mapped_column(
		Integer, nullable=False, default=0
	)
	json_before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
	json_after: Mapped[dict] = mapped_column(JSONB, nullable=False)
	assigned_moderator_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID(as_uuid=True), nullable=True
	)
	claimed_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True), nullable=True
	)
	blocking_reason_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID(as_uuid=True), nullable=True
	)
	moderator_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
	decision_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True), nullable=True
	)

	field_reports: Mapped[list["TicketFieldReport"]] = relationship(
		"TicketFieldReport",
		back_populates="ticket",
		cascade="all, delete-orphan",
	)
