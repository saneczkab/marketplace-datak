import uuid
from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Collection, CollectionProduct
from database.models import Product
from database.models import Sku


async def get_active_collections(
	db: AsyncSession, limit: int = 10, offset: int = 0
) -> Sequence[Collection]:
	"""Получить список активных подборок"""
	today = date.today()

	query = (
		select(Collection)
		.where(
			Collection.is_active == True,  # noqa
			(Collection.start_date <= today) | (Collection.start_date.is_(None)),
		)
		.order_by(Collection.priority)
		.offset(offset)
		.limit(limit)
	)
	result = await db.execute(query)
	return result.scalars().all()


async def count_active_collections(db: AsyncSession) -> int:
	"""Получить общее количество активных подборок"""
	today = date.today()

	query = select(func.count(Collection.id)).where(
		Collection.is_active == True,  # noqa
		(Collection.start_date <= today) | (Collection.start_date.is_(None)),
	)
	result = await db.execute(query)
	return result.scalar() or 0


async def get_collection_by_id(
	db: AsyncSession, collection_id: uuid.UUID
) -> Optional[Collection]:
	"""Получить подборку по ID"""
	query = select(Collection).where(Collection.id == collection_id)
	result = await db.execute(query)
	return result.scalar_one_or_none()


async def get_collection_product_ids(
	db: AsyncSession, collection_id: uuid.UUID
) -> Sequence[uuid.UUID]:
	"""Получить все ID товаров, привязанных к подборке"""
	query = select(CollectionProduct.product_id).where(
		CollectionProduct.collection_id == collection_id
	)
	result = await db.execute(query)
	return result.scalars().all()


async def get_products_by_ids(
	db: AsyncSession, product_ids: list[uuid.UUID], limit: int, offset: int
) -> Sequence[Product]:
	"""Получить детальную информацию о товарах с подгрузкой связей"""
	if not product_ids:
		return []

	query = (
		select(Product)
		.where(Product.id.in_(product_ids))
		.options(
			selectinload(Product.category),
			selectinload(Product.images),
			selectinload(Product.characteristics),
			selectinload(Product.skus).selectinload(Sku.characteristics),
		)
		.offset(offset)
		.limit(limit)
	)
	result = await db.execute(query)
	return result.scalars().all()
