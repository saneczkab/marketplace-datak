from typing import Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from exceptions import category as category_exceptions
from exceptions.database import DatabaseError
from crud import category as category_crud
from crud import product as product_crud
from database.models.catalog.base import Category


async def get_category_info_by_id(db: AsyncSession, category_id: str) -> Category:
	category_uuid = uuid.UUID(category_id)
	result = await category_crud.get_category_by_id(db, category_uuid)
	if not result:
		raise category_exceptions.CategoryNotFoundError(
			f"Category with id {category_id} not found"
		)
	return result


async def get_categories_tree(db: AsyncSession) -> dict:
	"""Gets categories tree from database

	Args:
		db (AsyncSession): Database session

	Raises:
		category_exceptions.CategoryNotFoundError: If no root category is found
				Most likely reason is empty database



	Returns:
		dict: Dictionary representing the categories tree
	"""

	result = await db.execute(select(Category).where(Category.parent_id.is_(None)))
	parent_category: Category | None = result.scalars().first()
	if not parent_category:
		raise category_exceptions.CategoryNotFoundError("No root category found")

	async def build_tree(category: Category) -> dict:
		children = await category_crud.get_categories_by_parent_id(db, category.id)
		return {
			"id": str(category.id),
			"name": category.name,
			"parent_id": str(category.parent_id) if category.parent_id else None,
			"children": [await build_tree(child) for child in children],
		}

	tree = await build_tree(parent_category)
	return tree


async def count_products_in_category(db: AsyncSession, category_id: uuid.UUID) -> int:

	category_uuid = uuid.UUID(
		str(category_id)
	)  # Will raise ValueError if category_id is not a valid UUID

	categories: list[uuid.UUID] = [category_uuid]
	queue: list[uuid.UUID] = [category_uuid]

	while queue:
		current_id: uuid.UUID = queue.pop(0)
		subcategories: list[Category] = await category_crud.get_categories_by_parent_id(
			db, current_id
		)
		for subcategory in subcategories:
			subcategory_id: uuid.UUID = subcategory.id
			categories.append(subcategory_id)
			queue.append(subcategory_id)

	count: int = 0

	for category_id in categories:
		count += await product_crud.count_products_in_category(db, category_id)

	return count


async def get_category_filters() -> dict:
	pass  # Will be implemented when filter are added to database


async def get_breadcrumbs(category_id: uuid.UUID) -> list[dict]:
	pass


async def get_facets(category_id: uuid.UUID) -> dict:
	pass
