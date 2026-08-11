from datetime import UTC, datetime
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_password_hash
from database.models import Seller


async def add_seller(seller: Seller, db: AsyncSession) -> Seller:
	db.add(seller)
	await db.commit()
	await db.refresh(seller)
	return seller


async def get_seller_by_email(email: str, db: AsyncSession) -> Seller | None:
	result = await db.execute(select(Seller).where(Seller.email == email))
	return result.scalar_one_or_none()


async def get_seller_by_id(seller_id: uuid.UUID, db: AsyncSession) -> Seller | None:
	result = await db.execute(select(Seller).where(Seller.id == seller_id))
	return result.scalar_one_or_none()


async def update_seller(
	seller: Seller, update_data: dict[str, Any], db: AsyncSession
) -> Seller:
	password = update_data.pop("password", None)
	if password is not None:
		update_data["password_hash"] = get_password_hash(password)

	for field, value in update_data.items():
		setattr(seller, field, value)

	seller.updated_at = datetime.now(UTC)
	await db.commit()
	await db.refresh(seller)
	return seller
