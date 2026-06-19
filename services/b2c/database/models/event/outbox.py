from database.core import Base

from sqlalchemy import DateTime, text, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from enum import Enum
import uuid
from datetime import datetime, timezone


class OutboxEventStatusEnum(str, Enum):
	PENDING = "PENDING"
	SENT = "SENT"


class OutboxEvent(Base):
	__tablename__ = "outbox_event"
	__table_args__ = {"schema": "events"}

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, server_default=text("get_random_uuid()")
	)
	idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
	event_type: Mapped[str] = mapped_column(String(32))
	payload: Mapped[dict] = mapped_column(JSONB)
	occurred_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=datetime.now(timezone.utc)
	)
