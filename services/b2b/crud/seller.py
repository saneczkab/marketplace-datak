from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Seller
from schemas.seller import SellerInfoPatch


async def add_seller(seller: Seller, db: AsyncSession) -> Seller:
	db.add(seller)
	await db.commit()
	await db.refresh(seller)
	return seller


async def get_seller_by_email(email: str, db: AsyncSession) -> Seller | None:
	result = await db.execute(select(Seller).where(Seller.email == email))
	seller = result.scalar_one_or_none()

	return seller


async def get_seller_by_id(id: UUID, db: AsyncSession) -> Seller | None:
	return (
		await db.execute(select(Seller).where(Seller.id == id))
	).scalar_one_or_none()


async def update_seller(
	seller_id: UUID, seller_info: SellerInfoPatch, db: AsyncSession
) -> Seller:
	# Existence of seller guaranted by auth
	seller: Seller = (
		await db.execute(select(Seller).where(Seller.id == seller_id))
	).scalar_one()

	seller.email = seller_info.email
	seller.phone = seller_info.phone
	seller.first_name = seller_info.first_name
	seller.last_name = seller_info.last_name
	seller.middle_name = seller_info.middle_name
	seller.company_name = seller_info.company_name
	seller.updated_at = datetime.now(UTC)

	await db.commit()

	return seller
