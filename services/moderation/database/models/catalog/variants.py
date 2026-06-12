from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.core import Base

if TYPE_CHECKING:
	from database.models.catalog.base import Product


class Sku(Base):
	__tablename__ = "skus"
	__table_args__ = {"schema": "catalog"}

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	product_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("catalog.products.id", ondelete="CASCADE"), nullable=False
	)
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	price: Mapped[int] = mapped_column(BigInteger, nullable=False)
	discount: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
	active_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
	article: Mapped[str | None] = mapped_column(String(255), nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)

	product: Mapped[Product] = relationship("Product", back_populates="skus")
	images: Mapped[list[Image]] = relationship(
		"Image",
		back_populates="sku",
		cascade="all, delete-orphan",
		foreign_keys="Image.sku_id",
	)
	characteristics: Mapped[list[Characteristic]] = relationship(
		"Characteristic",
		back_populates="sku",
		cascade="all, delete-orphan",
		foreign_keys="Characteristic.sku_id",
	)


class Characteristic(Base):
	__tablename__ = "characteristics"
	__table_args__ = {"schema": "catalog"}

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	product_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("catalog.products.id", ondelete="CASCADE"), nullable=True
	)
	sku_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("catalog.skus.id", ondelete="CASCADE"), nullable=True
	)
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	value: Mapped[str] = mapped_column(String(255), nullable=False)

	product: Mapped[Product | None] = relationship(
		"Product", back_populates="characteristics", foreign_keys=[product_id]
	)
	sku: Mapped[Sku | None] = relationship(
		"Sku", back_populates="characteristics", foreign_keys=[sku_id]
	)


class Image(Base):
	__tablename__ = "images"
	__table_args__ = {"schema": "catalog"}

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	product_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("catalog.products.id", ondelete="CASCADE"), nullable=True
	)
	sku_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("catalog.skus.id", ondelete="CASCADE"), nullable=True
	)
	url: Mapped[str] = mapped_column(String(512), nullable=False)
	ordering: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

	product: Mapped[Product | None] = relationship(
		"Product", back_populates="images", foreign_keys=[product_id]
	)
	sku: Mapped[Sku | None] = relationship(
		"Sku", back_populates="images", foreign_keys=[sku_id]
	)
