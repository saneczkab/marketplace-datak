import uuid
from schemas.category import (
	CategoryInfoResponse,
	CategoryParent,
	CategoryTreeResponse,
	CategoryNode,
)
from exceptions.category import CategoryNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

import crud.category as category_crud
import crud.product as product_crud


async def get_category_info(
	db: AsyncSession, id: str, include_product_count: bool
) -> CategoryInfoResponse:
	id: uuid.UUID = uuid.UUID(id)  # Raises ValueError if invalid

	category = await category_crud.get_category_by_id(db, id)
	if not category:
		raise CategoryNotFoundError(f"Category with id {id} not found")

	if category.parent_id:
		parent_category = await category_crud.get_category_by_id(db, category.parent_id)
		parent_info = CategoryParent(
			id=parent_category.id, name=parent_category.name, slug=parent_category.slug
		)

	return CategoryInfoResponse(
		id=category.id,
		name=category.name,
		slug=category.slug,
		description=category.description,
		parent=parent_info if category.parent_id else None,
		product_count=await category_product_count(db, id)
		if include_product_count
		else None,
		seo=None,  # TODO implement  # noqa
		meta=None,  # TODO implement # noqa
		image_url=category.image_url,
		is_active=category.is_active,
		created_at=category.created_at.isoformat(),
		updated_at=category.updated_at.isoformat(),
	)


async def category_product_count(db: AsyncSession, category_id: uuid.UUID) -> int:
	categories: list[uuid.UUID] = [category_id]
	subcategories = await category_crud.get_categories_by_parent_id(db, category_id)
	while subcategories:
		subcategory_ids = [subcategory.id for subcategory in subcategories]
		categories.extend(subcategory_ids)
		subcategories = await category_crud.get_categories_by_parent_id(db, category_id)

	count = 0
	for cat_id in categories:
		count += await product_crud.count_products_in_category(db, cat_id)
	return count


async def get_categories_tree(db: AsyncSession) -> CategoryTreeResponse:
	root_category_all = await category_crud.get_categories_by_parent_id(db, None)
	root_category = root_category_all[0] if root_category_all else None
	if not root_category:
		raise CategoryNotFoundError("No root category found")

	result = CategoryTreeResponse(
		items=[
			CategoryNode(
				id=root_category.id,
				name=root_category.name,
				parent_id=root_category.parent_id,
				children=[],
			)
		]
	)

	await build_category_tree(db, result.items[0])
	return result


async def build_category_tree(db: AsyncSession, node: CategoryNode) -> None:
	subcategories = await category_crud.get_categories_by_parent_id(db, node.id)
	for subcategory in subcategories:
		child_node = CategoryNode(
			id=subcategory.id,
			name=subcategory.name,
			parent_id=subcategory.parent_id,
			children=[],
		)
		node.children.append(child_node)
		await build_category_tree(db, child_node)
