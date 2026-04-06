import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from exceptions import category as category_exceptions
from crud import category as category_crud
from database.models.catalog.base import Category


async def get_category_by_id(db: AsyncSession, category_id: uuid.UUID) -> Category:
	"""Gets category by its id

	Args:
	    db (AsyncSession): Database session
	    category_id (uuid.UUID): The ID of the category to retrieve

	Raises:
	    category_exceptions.CategoryNotFoundError: If the category with the specified ID is not found

	Returns:
	    Category: The retrieved category
	"""
	category: Category | None = await category_crud.get_category_by_id(db, category_id)
	if not category:
		raise category_exceptions.CategoryNotFoundError(
			f"Category with id {category_id} not found"
		)
	return category


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
