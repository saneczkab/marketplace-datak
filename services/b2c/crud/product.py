from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from database.models import Sku
from database.models.catalog.base import Product
from schemas.sku import Sku as SkuSchema


async def count_products_in_category(db: AsyncSession, category_id: uuid.UUID) -> int:
	result = await db.execute(select(Product).where(Product.category_id == category_id))
	return result.scalar() or 0


async def get_product_skus(
	db: AsyncSession, product_id: uuid.UUID
) -> List[SkuSchema] | None:
	"""
	Returns a list of skus for a given product ID.
	:param db: database session
	:param product_id: product ID
	:return: list of skus or None if not found
	"""
	result = await db.execute(select(Sku).where(Sku.product_id == product_id))
	return list(result.scalars().all())
