from database.core import Base

import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import DateTime, String, func


class InboxEventStatusEnum(str, Enum):
	PENDING = "PENDING"
	PROCESSED = "PROCESSED"
	FAILED = "FAILED"


class InboxEvent(Base):
	__tablename__ = "inbox_events"
	__table_args__ = {"schema": "events"}

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
	routing_key: Mapped[str] = mapped_column(String(255))
	payload: Mapped[dict] = mapped_column(JSONB)
	status: Mapped[InboxEventStatusEnum] = mapped_column(
		default=InboxEventStatusEnum.PENDING
	)
	event_type: Mapped[str] = mapped_column(String(32))
	occured_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False
	)

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now()
	)
	processed_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=True
	)
