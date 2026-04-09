from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from database.models import Sku
from database.models.catalog.base import Product
from exceptions.product import ProductNotFoundError
from schemas.sku import Sku as SkuSchema


async def count_products_in_category(db: AsyncSession, category_id: uuid.UUID) -> int:
	result = await db.execute(select(Product).where(Product.category_id == category_id))
	return result.scalars().count()


async def get_product_skus(db: AsyncSession, product_id: uuid.UUID) -> List[SkuSchema]:
	"""
	Returns a list of skus for a given product ID.
	:param db: database session
	:param product_id: product ID
	:return: list of skus
	:throws: ProductNotFoundError if not found
	"""
	result = await db.execute(select(Sku).where(Sku.product_id == product_id))
	skus: list[SkuSchema] = list(result.scalars().all())

	if not skus:
		raise ProductNotFoundError()

	return skus
