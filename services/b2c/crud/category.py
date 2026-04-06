from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID, select
import uuid
from database.models.catalog.base import Category, Product


# TODO: Raise error if db is unavailable

async def get_category_by_id(
	db: AsyncSession, category_id: uuid.UUID
) -> Category | None:
	result = await db.execute(select(Category).where(Category.id == category_id))
	return result.scalars().first()


async def get_categories_by_parent_id(
	db: AsyncSession, parent_id: uuid.UUID | None
) -> list[Category]:
	result = await db.execute(select(Category).where(Category.parent_id == parent_id))
	return result.scalars().all()


async def count_products_in_category(db: AsyncSession, category_id: uuid.UUID) -> int:
	categories: list[uuid.UUID] = [category_id]
	queue: list[UUID] = [category_id]

	while queue:
		current_id = queue.pop(0)
		subcategories = await get_categories_by_parent_id(db, current_id)
		for subcategory in subcategories:
			subcategory_id = subcategory.id
			categories.append(subcategory_id)
			queue.append(subcategory_id)

	count: int = 0

	for category_id in categories:
		count += await db.execute(
			select(Product).where(Category.id == category_id)
		).rowcount

	return count