import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from exceptions import category as category_exceptions
from crud import category as category_crud
from database.models.catalog.base import Category


async def get_category_info_by_id(
	db: AsyncSession, category_id: uuid.UUID, need_count: bool = False
) -> Category:
	category_uuid = uuid.UUID(
		str(category_id)
	)  # Will raise ValueError if category_id is not a valid UUID
	category: Category | None = await db.execute(
		select(Category).where(Category.id == category_uuid)
	).first()
	if not category:
		raise category_exceptions.CategoryNotFoundError("Category not found")

	parent: Category | None = None
	if category.parent_id:
		parent = await get_category_info_by_id(db, category.parent_id) # TODO ХУЙНЯ ПЕРЕДЕЛАТЬ

	# Count products in category if needed
	# Otherwise, set count to None
	product_count: int | None = None
	if need_count:
		product_count = await category_crud.count_products_in_category(db, category.id)
	return {
		"id": str(category.id),
		"name": category.name,
		"slug": category.slug,
		"description": category.description,
		"parent": {
			"id": str(category.parent_id) if category.parent_id else None,
			"name": parent.name if parent else None,
			"slug": parent.slug if parent else None,
		},
		"product_count": product_count,
	}


async def get_categories_tree(db: AsyncSession) -> str:
	"""Gets categories tree from database

	Args:
	    db (AsyncSession): Database session

	Raises:
	    category_exceptions.CategoryNotFoundError: If no root category is found
	            Most likely reason is empty database

	Returns:
	    str: JSON string representing the categories tree
	"""
	result = await db.execute(select(Category).where(Category.parent_id is None))
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
	return json.dumps(tree)
