import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from exceptions import category as category_exceptions
from exceptions.database import DatabaseError
from crud import category as category_crud
from crud import product as product_crud
from database.models.catalog.base import Category


async def get_category_info_by_id(
	db: AsyncSession, category_id: uuid.UUID, need_count: bool = False
) -> Category:
	try:
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
			parent = await category_crud.get_categories_by_parent_id(
				db, category.parent_id
			)

		# Count products in category if needed
		# Otherwise, set count to None
		product_count: int | None = None
		if need_count:
			product_count = await category_crud.count_products_in_category(
				db, category.id
			)
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
			"seo": None,  # TODO: Add SEO fields to Category model and return them here # noqa: FIX002
			"created_at": category.created_at.isoformat(),
			"is_active": category.is_active,
		}
	except DatabaseError as db_err:
		raise category_exceptions.CategoryError("Database error occurred") from db_err


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
	try:
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
	except DatabaseError as db_err:
		raise category_exceptions.CategoryError("Database error occurred") from db_err


async def count_products_in_category(db: AsyncSession, category_id: uuid.UUID) -> int:
	try:
		category_uuid = uuid.UUID(
			str(category_id)
		)  # Will raise ValueError if category_id is not a valid UUID

		categories: list[uuid.UUID] = [category_uuid]
		queue: list[uuid.UUID] = [category_uuid]

		while queue:
			current_id: uuid.UUID = queue.pop(0)
			subcategories: list[
				Category
			] = await category_crud.get_categories_by_parent_id(db, current_id)
			for subcategory in subcategories:
				subcategory_id: uuid.UUID = subcategory.id
				categories.append(subcategory_id)
				queue.append(subcategory_id)

		count: int = 0

		for category_id in categories:
			count += await product_crud.count_products_in_category(db, category_id)

		return count
	except DatabaseError as db_err:
		raise category_exceptions.CategoryError("Database error occurred") from db_err


async def get_category_filters() -> dict:
	pass  # Will be implemented when filter are added to database


async def get_breadcrumbs(category_id: uuid.UUID) -> list[dict]:
	pass


async def get_facets(category_id: uuid.UUID) -> dict:
	pass
