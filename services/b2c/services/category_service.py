import uuid
from schemas.category import (
	BreadcrumbItem,
	BreadcrumbMeta,
	BreadcrumbResponse,
	CategoryInfoResponse,
	CategoryParent,
	CategoryTreeResponse,
	CategoryNode,
	FacetsResponse,
	Facet,
	FacetValue,
	FilterResponse,
	ResolveViaEnum,
)
from exceptions.category import CategoryNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

import crud.category as category_crud
import crud.product as product_crud
from database.models.catalog.base import Category


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


async def get_category_filters(db: AsyncSession, category_id: str) -> FilterResponse:
	id: uuid.UUID = uuid.UUID(category_id)

	category = await category_crud.get_category_by_id(db, id)
	if not category:
		raise CategoryNotFoundError(f"Category with id {id} not found")

	filters = await category_crud.get_category_filters(db, id)

	filters_schemas = [
		FilterResponse(
			id=filter.id,
			name=filter.name,
			type=filter.type,
			value=await category_crud.get_filter_values(db, filter.id)
			if filter.type == "LIST"
			else None,
			min=filter.min,
			max=filter.max,
		)
		for filter in filters
	]

	return FilterResponse(items=filters_schemas)


async def get_category_facets(
	db: AsyncSession, category_id: str, filters: str | None = None
) -> FacetsResponse:
	id: uuid.UUID = uuid.UUID(category_id)
	# Возвращает список фасетов (фильтров) для указанной категории и для каждого значения — количество товаров (count), соответствующих этому значению при текущих применённых фильтрах. Вызывается при загрузке страницы категории и при каждом изменении фильтров на клиенте (чтобы обновить счётчики рядом с опциями фильтров).
	category = await category_crud.get_category_by_id(db, id)
	if not category:
		raise CategoryNotFoundError(f"Category with id {id} not found")

	category_uuid: uuid.UUID = uuid.UUID(category_id)

	available_filters: FilterResponse = await category_crud.get_category_filters(
		db, category_uuid
	)

	if not filters:
		facets: list[Facet] = []
		for filter in available_filters.items:
			facet_values: list[FacetValue] = []
			if filter.type == "LIST":
				for value in filter.value:
					count = await product_crud.count_products_by_filter(
						db, category_uuid, filter.id, value
					)
					facet_values.append(FacetValue(value=value, count=count))
			facets.append(Facet(name=filter.name, values=facet_values))

	# TODO implement if filters are given # noqa
	# TODO what to do if type isn't LIST? # noqa
	return FacetsResponse(category_id=category_uuid, facets=[])


async def get_category_breadcrumbs(
	db: AsyncSession, category_id: str | None, product_id: str | None
) -> BreadcrumbResponse:
	if not category_id and not product_id:
		raise ValueError("Either category_id or product_id must be provided")

	if category_id and product_id:
		raise ValueError("Only one of category_id or product_id should be provided")

	flag: bool = True if product_id else False

	if flag:
		category_id: uuid.UUID = await product_crud.get_product_category_id(
			db, uuid.UUID(product_id)
		)
	else:
		category_id: uuid.UUID = uuid.UUID(category_id)

	category: Category = await category_crud.get_category_by_id(db, category_id)

	level: int = 1
	url: str = category.slug

	while category.parent_id:
		category = await category_crud.get_category_by_id(db, category.parent_id)
		url = category.slug + "/" + url
		level += 1

	return BreadcrumbResponse(
		BreadcrumbItem(
			id=uuid.UUID(category_id),
			slug="",  # Todo What should be here? # noqa
			name=category.name,
			url=url,
			level=level,
			is_current=True,
		),
		BreadcrumbMeta(
			resolved_via=ResolveViaEnum.PRODUCT if flag else ResolveViaEnum.CATEGORY,
			category_id=category_id if flag else None,
			product_id=uuid.UUID(product_id) if flag else None,
		),
	)
