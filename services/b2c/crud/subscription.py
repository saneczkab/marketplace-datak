import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.personal import Subscription
from database.models.catalog.base import Product
from database.models.catalog.variants import Sku


async def get_subscription(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> Optional[Subscription]:
	"""Проверить, существует ли уже подписка у юзера на этот товар"""
	query = select(Subscription).where(
		Subscription.user_id == user_id, Subscription.product_id == product_id
	)
	result = await db.execute(query)
	return result.scalar_one_or_none()


async def create_subscription(
	db: AsyncSession,
	user_id: uuid.UUID,
	product_id: uuid.UUID,
	notify_in_stock: bool,
	notify_price_down: bool,
) -> Subscription:
	"""Создать новую подписку в БД"""
	subscription = Subscription(
		user_id=user_id,
		product_id=product_id,
		notify_in_stock=notify_in_stock,
		notify_price_down=notify_price_down,
	)
	db.add(subscription)
	await db.commit()
	await db.refresh(subscription)
	return subscription


async def get_product_for_subscription(
	db: AsyncSession, product_id: uuid.UUID
) -> Optional[Product]:
	"""Получить товар со всеми связями для формирования ответа"""
	query = (
		select(Product)
		.where(Product.id == product_id)
		.options(
			selectinload(Product.images),
			selectinload(Product.characteristics),
			selectinload(Product.category),
			selectinload(Product.skus).selectinload(Sku.characteristics),
		)
	)
	result = await db.execute(query)
	return result.scalar_one_or_none()


async def delete_subscription(db: AsyncSession, subscription: Subscription) -> None:
	"""Удалить подписку из базы"""
	await db.delete(subscription)
	await db.commit()
