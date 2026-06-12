import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.core import Base


class ProcessedB2BEvent(Base):
	__tablename__ = "processed_b2b_events"

	sender_service: Mapped[str] = mapped_column(String(64), primary_key=True)
	idempotency_key: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True
	)
	product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
	event_type: Mapped[str] = mapped_column(String(32), nullable=False)
	processed_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
