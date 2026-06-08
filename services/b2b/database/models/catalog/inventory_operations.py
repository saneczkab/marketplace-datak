import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.core import Base


class InventoryReserveOperation(Base):
	__tablename__ = "inventory_reserve_operations"
	__table_args__ = {"schema": "catalog"}

	idempotency_key: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True
	)
	order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
	result: Mapped[dict] = mapped_column(JSONB, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now()
	)


class InventoryUnreserveOperation(Base):
	__tablename__ = "inventory_unreserve_operations"
	__table_args__ = {"schema": "catalog"}

	order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	processed_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now()
	)
