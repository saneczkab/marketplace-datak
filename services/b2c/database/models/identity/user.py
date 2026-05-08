import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.core import Base

if TYPE_CHECKING:
	from database.models.cart.item import CartItem
	from database.models.personal.profile import Favorite, Subscription


class User(Base):
	__tablename__ = "users"
	__table_args__ = {"schema": "identity"}

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
	)
	username: Mapped[str] = mapped_column(unique=True, nullable=False)
	email: Mapped[str] = mapped_column(unique=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now()
	)

	# Relationships
	cart_items: Mapped[list["CartItem"]] = relationship(
		"CartItem", back_populates="user", foreign_keys="CartItem.user_id"
	)
	favorites: Mapped[list["Favorite"]] = relationship(
		"Favorite", back_populates="user"
	)
	subscriptions: Mapped[list["Subscription"]] = relationship(
		"Subscription", back_populates="user"
	)
