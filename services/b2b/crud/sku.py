from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud import images as images_crud
from crud import outbox as outbox_crud
from crud import product as product_crud
from database.models import Characteristic, Sku
from database.models.catalog.base import Product, ProductStatusEnum
from database.models.catalog.variants import Image


async def create(
	db: AsyncSession,
	data: dict,
	product: Product,
) -> Sku:
	chars_data = data.pop("characteristics", []) or []
	data.pop("images", None)
	data.pop("product_id", None)

	sku = Sku(product_id=product.id, **data)
	db.add(sku)
	await db.flush()

	for char in chars_data:
		char_fields = {"name": char["name"], "value": char["value"]}
		db.add(Characteristic(**char_fields, sku_id=sku.id))

	await db.commit()
	return await get_sku_by_id(db, sku.id)


async def transition_product_to_on_moderation(
	db: AsyncSession, product: Product
) -> None:
	product.status = ProductStatusEnum.ON_MODERATION
	db.add(product)
	await db.commit()
	await db.refresh(product)


async def get_sku_by_id(db: AsyncSession, sku_id: UUID) -> Sku | None:
	result = await db.execute(
		select(Sku).options(joinedload(Sku.characteristics)).where(Sku.id == sku_id)
	)
	return result.unique().scalar_one_or_none()


async def get_sku_and_product(
	db: AsyncSession, sku_id: UUID
) -> tuple[Sku, Product] | None:
	sku = await get_sku_by_id(db, sku_id)
	if sku is None:
		return None
	product = await product_crud.get_product_by_id_only(db, sku.product_id)
	if product is None:
		return None
	return sku, product


async def attach_sku_image_with_moderation(
	db: AsyncSession,
	sku: Sku,
	product: Product,
	url: str,
	ordering: int,
	submit_for_moderation: bool,
) -> Image:
	image = await images_crud.attach_sku_image(db, sku.id, url, ordering)

	if submit_for_moderation:
		product.status = ProductStatusEnum.ON_MODERATION
		db.add(product)
		await outbox_crud.enqueue_moderation_product_created(
			db,
			product_id=product.id,
			seller_id=product.seller_id,
		)

	await db.commit()
	await db.refresh(image)
	return image


async def get_by_product_id(db: AsyncSession, product_id: UUID) -> list[Sku]:
	result = await db.execute(
		select(Sku)
		.options(joinedload(Sku.characteristics))
		.where(Sku.product_id == product_id)
	)
	return list(result.unique().scalars().all())


async def update(db: AsyncSession, sku_id: UUID, data: dict) -> Sku | None:
	sku = await get_sku_by_id(db, sku_id)
	if not sku:
		return None

	data.pop("product_id", None)
	data.pop("characteristics", None)
	data.pop("images", None)

	for key, value in data.items():
		setattr(sku, key, value)

	await db.commit()
	await db.refresh(sku)
	return sku


async def count_skus_by_product_id(db: AsyncSession, product_id: UUID) -> int:
	result = await db.execute(
		select(func.count()).select_from(Sku).where(Sku.product_id == product_id)
	)
	return int(result.scalar_one())


async def load_images_for_sku(db: AsyncSession, sku_id: UUID) -> list[Image]:
	return await images_crud.get_sku_images_by_id(sku_id, db)
