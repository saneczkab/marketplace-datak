from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from crud import outbox as outbox_crud
from database.models.catalog.base import Product, ProductStatusEnum
from database.models.catalog.variants import Characteristic


async def submit_for_moderation(
	db: AsyncSession,
	product: Product,
	event: str = "CREATED",
) -> None:
	product.status = ProductStatusEnum.ON_MODERATION
	db.add(product)
	await outbox_crud.enqueue_moderation_product_created(
		db,
		product_id=product.id,
		seller_id=product.seller_id,
		event=event,
	)


async def add_product(product: Product, db: AsyncSession) -> Product:
	db.add(product)
	await db.commit()
	await db.refresh(product)
	return product


async def get_seller_products(db: AsyncSession, seller_id: UUID) -> list[Product]:
	result = await db.execute(select(Product).where(Product.seller_id == seller_id))
	return list(result.scalars().all())


async def get_product_by_id(
	db: AsyncSession, product_id: UUID, seller_id: UUID
) -> Product | None:
	result = await db.execute(
		select(Product).where(Product.id == product_id, Product.seller_id == seller_id)
	)
	return result.scalar_one_or_none()


async def get_product_by_id_only(db: AsyncSession, product_id: UUID) -> Product | None:
	result = await db.execute(select(Product).where(Product.id == product_id))
	return result.scalar_one_or_none()


async def get_product_characteristics(
	db: AsyncSession, product_id: UUID
) -> list[Characteristic]:
	result = await db.execute(
		select(Characteristic).where(
			Characteristic.product_id == product_id,
			Characteristic.sku_id.is_(None),
		)
	)
	return list(result.scalars().all())


async def update_product(
	db: AsyncSession,
	db_obj: Product,
	update_data: dict,
	should_remoderate: bool = False,
) -> Product:
	for field, value in update_data.items():
		setattr(db_obj, field, value)

	db.add(db_obj)
	if should_remoderate:
		await submit_for_moderation(db, db_obj, event="EDITED")

	await db.commit()
	await db.refresh(db_obj)
	return db_obj


async def soft_delete_product(db: AsyncSession, db_obj: Product) -> Product:
	db_obj.status = ProductStatusEnum.DELETED
	db.add(db_obj)
	await db.commit()
	await db.refresh(db_obj)
	return db_obj


async def hard_delete_product(db: AsyncSession, db_obj: Product) -> None:
	await db.delete(db_obj)
	await db.commit()
