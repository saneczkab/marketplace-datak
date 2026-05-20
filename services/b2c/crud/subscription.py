import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Subscription
from database.models import Product


async def get_subscription(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> Optional[Subscription]:
	query = select(Subscription).where(
		Subscription.user_id == user_id, Subscription.product_id == product_id
	)
	result = await db.execute(query)
	return result.scalar_one_or_none()


async def product_exists(db: AsyncSession, product_id: uuid.UUID) -> bool:
	result = await db.execute(select(Product.id).where(Product.id == product_id))
	return result.scalar_one_or_none() is not None


async def upsert_subscription(
	db: AsyncSession,
	user_id: uuid.UUID,
	product_id: uuid.UUID,
	notify_in_stock: bool,
	notify_price_down: bool,
) -> None:
	existing = await get_subscription(db, user_id, product_id)
	if existing:
		existing.notify_in_stock = notify_in_stock
		existing.notify_price_down = notify_price_down
	else:
		db.add(
			Subscription(
				user_id=user_id,
				product_id=product_id,
				notify_in_stock=notify_in_stock,
				notify_price_down=notify_price_down,
			)
		)
	await db.commit()


async def delete_subscription_by_product(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> None:
	subscription = await get_subscription(db, user_id, product_id)
	if subscription:
		await db.delete(subscription)
		await db.commit()
