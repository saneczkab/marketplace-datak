from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_password_hash
from models.seller import Seller


async def get_seller_by_id(db: AsyncSession, seller_id: str) -> Seller | None:
	result = await db.execute(select(Seller).where(Seller.id == seller_id))
	return result.scalar_one_or_none()


async def get_seller_by_email(db: AsyncSession, email: str) -> Seller | None:
	result = await db.execute(select(Seller).where(Seller.email == email))
	return result.scalar_one_or_none()


async def update_seller(
	db: AsyncSession, seller: Seller, update_data: dict[str, Any]
) -> Seller:
	if password := update_data.pop("password", None):
		update_data["password_hash"] = get_password_hash(password)

	for field, value in update_data.items():
		setattr(seller, field, value)

	seller.updated_at = datetime.now(UTC)
	await db.commit()
	await db.refresh(seller)
	return seller
