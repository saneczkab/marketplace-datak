from enum import Enum
import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from database.core import Base

from sqlalchemy import (
	DateTime,
	func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID


class EventTypeEnum(str, Enum):
	PRODUCT_BLOCKED = "PRODUCT_BLOCKED"
	PRODUCT_HARD_BLOCKED = "PRODUCT_HARD_BLOCKED"
	PRODUCT_DELETED = "PRODUCT_DELETED"
	SKU_OUT_OF_STOCK = "SKU_OUT_OF_STOCK"
	PRICE_CHANGED = "PRICE_CHANGED"


class B2BEvent(Base):
	"""Class used to save handled events by idempotency key"""

	__tablename__ = "b2b_events"
	__table_args__ = {"schema": "events"}
	idempotency_key: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True
	)
	event_type: Mapped[EventTypeEnum] = mapped_column(
		SQLEnum(EventTypeEnum, name="eventtypeenum", schema="events")
	)  # Do i really need this?
	issued_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now()
	)  # TTL = 1hrs
