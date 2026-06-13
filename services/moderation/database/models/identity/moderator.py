import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.core import Base


class ModeratorRole(str, enum.Enum):
	MODERATOR = "MODERATOR"
	ADMIN = "ADMIN"


class Moderator(Base):
	__tablename__ = "moderators"
	__table_args__ = {"schema": "identity"}

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
	)
	email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(nullable=False)
	first_name: Mapped[str] = mapped_column(nullable=False)
	last_name: Mapped[str | None] = mapped_column(nullable=True)
	role: Mapped[ModeratorRole] = mapped_column(
		Enum(ModeratorRole, name="moderator_role", native_enum=False),
		nullable=False,
		default=ModeratorRole.MODERATOR,
	)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	category_specializations: Mapped[list[uuid.UUID] | None] = mapped_column(
		ARRAY(UUID(as_uuid=True)), nullable=True
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	last_login_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True), nullable=True
	)


class Session(Base):
	__tablename__ = "sessions"
	__table_args__ = {"schema": "identity"}

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
	)
	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("identity.moderators.id"), nullable=False
	)
	access_token: Mapped[str] = mapped_column(unique=True, nullable=False)
	refresh_token: Mapped[str] = mapped_column(unique=True, nullable=False)
	issued_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	expires_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False
	)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
