from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID
from database.models import Sku, Characteristic, Image


async def create(db: AsyncSession, data: dict) -> Sku:
	"""Create a new SKU with its characteristics and images."""
	chars_data = data.pop("characteristics", [])
	images_data = data.pop("images", [])

	sku = Sku(**data)
	db.add(sku)
	await db.flush()

	if chars_data:
		for char in chars_data:
			db.add(Characteristic(**char, sku_id=sku.id))

	if images_data:
		for img in images_data:
			db.add(Image(**img, sku_id=sku.id))

	await db.commit()
	return await get_sku_by_id(db, sku.id)


async def get_sku_by_id(db: AsyncSession, sku_id: UUID) -> Sku | None:
	"""Get a single SKU by its ID with all related data."""
	result = await db.execute(
		select(Sku)
		.options(joinedload(Sku.characteristics), joinedload(Sku.images))
		.filter(Sku.id == sku_id)
	)
	return result.unique().scalar_one_or_none()


async def get_by_product_id(db: AsyncSession, product_id: UUID) -> list[Sku]:
	"""Get all SKUs associated with a specific product."""
	result = await db.execute(
		select(Sku)
		.options(joinedload(Sku.characteristics), joinedload(Sku.images))
		.filter(Sku.product_id == product_id)
	)
	return list(result.unique().scalars().all())


async def update(db: AsyncSession, sku_id: UUID, data: dict) -> Sku | None:
	"""Update SKU fields."""
	sku = await get_sku_by_id(db, sku_id)
	if not sku:
		return None

	for key, value in data.items():
		setattr(sku, key, value)

	await db.commit()
	await db.refresh(sku)
	return sku
