from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.core import Base

if TYPE_CHECKING:
	from database.models.catalog.variants import Characteristic, Image, Sku


class ProductStatusEnum(str, enum.Enum):
	CREATED = "CREATED"
	ON_MODERATION = "ON_MODERATION"
	MODERATED = "MODERATED"
	BLOCKED = "BLOCKED"
	HARD_BLOCKED = "HARD_BLOCKED"
	DELETED = "DELETED"


class Category(Base):
	__tablename__ = "categories"
	__table_args__ = {"schema": "catalog"}

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	name: Mapped[str] = mapped_column(String(255), nullable=False)


class Product(Base):
	__tablename__ = "products"
	__table_args__ = {"schema": "catalog"}

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
	category_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("catalog.categories.id"), nullable=False
	)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	slug: Mapped[str] = mapped_column(String(255), nullable=False)
	description: Mapped[str | None] = mapped_column(Text, nullable=True)
	status: Mapped[ProductStatusEnum] = mapped_column(
		Enum(ProductStatusEnum, name="product_status", native_enum=False),
		default=ProductStatusEnum.CREATED,
		server_default="CREATED",
	)
	deleted: Mapped[bool] = mapped_column(
		Boolean, default=False, server_default="false"
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)

	category: Mapped["Category"] = relationship("Category", lazy="selectin")
	skus: Mapped[list["Sku"]] = relationship(
		"Sku", back_populates="product", cascade="all, delete-orphan"
	)
	images: Mapped[list["Image"]] = relationship(
		"Image",
		back_populates="product",
		cascade="all, delete-orphan",
		foreign_keys="Image.product_id",
	)
	characteristics: Mapped[list["Characteristic"]] = relationship(
		"Characteristic",
		back_populates="product",
		cascade="all, delete-orphan",
		foreign_keys="Characteristic.product_id",
	)
