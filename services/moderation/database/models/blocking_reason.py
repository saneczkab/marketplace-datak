import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.core import Base


class BlockingReason(Base):
	__tablename__ = "blocking_reasons"

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
	)
	code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
	title: Mapped[str] = mapped_column(String(200), nullable=False)
	description: Mapped[str | None] = mapped_column(Text, nullable=True)
	hard_block: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
