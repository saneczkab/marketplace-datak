import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.core import Base


class OutboxEventStatusEnum(str, enum.Enum):
	PENDING = "PENDING"
	SENT = "SENT"


class OutboxEvent(Base):
	__tablename__ = "outbox_event"
	__table_args__ = {"schema": "events"}

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, server_default=text("get_random_uuid()")
	)
	routing_key: Mapped[str] = mapped_column(String(32), nullable=False)
	idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
	event_type: Mapped[str] = mapped_column(String(32))
	payload: Mapped[dict] = mapped_column(JSONB)
	status: Mapped[OutboxEventStatusEnum] = mapped_column(
		server_default=OutboxEventStatusEnum.PENDING
	)
	occurred_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=datetime.now(timezone.utc)
	)
	sent_at: Mapped[datetime] = mapped_column(nullable=True)
