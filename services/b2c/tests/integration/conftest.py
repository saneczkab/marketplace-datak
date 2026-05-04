import uuid
from dataclasses import dataclass

import pytest
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import (
	Category,
	CategoryFilters,
	FilterTypeEnum,
	FilterValues,
	Product,
	ProductStatusEnum,
)
from database.models.catalog.variants import Sku
from tests.factories.catalog import (
	CategoryFactory,
	CategoryFiltersFactory,
	FilterValuesFactory,
	ProductFactory,
)


def _fixed_uuid() -> uuid.UUID:
	return uuid.uuid4()


@dataclass(frozen=True, slots=True)
class CategoriesTreeData:
	root: Category
	child: Category
	grandchild: Category


@pytest.fixture()
async def categories_tree(
	db_session: AsyncSession,
) -> CategoriesTreeData:
	"""
	Create categories tree test data.
	"""
	root = CategoryFactory.build(
		id=_fixed_uuid(), parent_id=None, name="Электроника", slug="electronics"
	)
	child = CategoryFactory.build(
		id=_fixed_uuid(), parent_id=root.id, name="Смартфоны", slug="smartphones"
	)
	grandchild = CategoryFactory.build(
		id=_fixed_uuid(), parent_id=child.id, name="Android", slug="android"
	)

	db_session.add_all([root, child, grandchild])
	await db_session.commit()
	return CategoriesTreeData(root=root, child=child, grandchild=grandchild)


@dataclass(frozen=True, slots=True)
class OrphanCategoryData:
	orphan: Category
	missing_parent_id: uuid.UUID


@pytest.fixture()
async def orphan_category(
	db_session: AsyncSession,
) -> OrphanCategoryData:
	"""
	Create orphan category test data.
	Sets session replication role to replica to avoid foreign key constraints errors. Needs for orphan category.
	"""
	missing_parent_id = _fixed_uuid()
	await db_session.execute(text("SET session_replication_role = replica"))
	orphan = CategoryFactory.build(
		id=_fixed_uuid(),
		parent_id=missing_parent_id,
		name="Orphan",
		slug="orphan",
	)
	db_session.add(orphan)
	await db_session.commit()
	await db_session.execute(text("SET session_replication_role = DEFAULT"))
	await db_session.commit()
	return OrphanCategoryData(orphan=orphan, missing_parent_id=missing_parent_id)


@dataclass(frozen=True, slots=True)
class CategoryWithProductsData:
	category: Category
	filters: tuple[CategoryFilters, CategoryFilters]
	values: tuple[FilterValues, FilterValues]
	products: tuple[Product, Product]


@pytest.fixture()
async def category_with_products(
	db_session: AsyncSession,
) -> CategoryWithProductsData:
	"""
	Create category with filters test data.
	"""
	category = CategoryFactory.build(
		id=_fixed_uuid(),
		name="Category with Filters",
		slug="category-with-filters",
	)
	filter_1 = CategoryFiltersFactory.build(
		id=_fixed_uuid(),
		category_id=category.id,
		name="Filter 1",
		slug="filter-1",
		type=FilterTypeEnum.LIST,
		value="Value 1",
	)
	filter_2 = CategoryFiltersFactory.build(
		id=_fixed_uuid(),
		category_id=category.id,
		name="Filter 2",
		slug="filter-2",
		type=FilterTypeEnum.LIST,
		value="Value 2",
	)
	filter_value_1 = FilterValuesFactory.build(
		id=_fixed_uuid(), filter_id=filter_1.id, value="Value 1"
	)
	filter_value_2 = FilterValuesFactory.build(
		id=_fixed_uuid(), filter_id=filter_2.id, value="Value 2"
	)
	product_1 = ProductFactory.build(
		id=_fixed_uuid(),
		category_id=category.id,
		title="Product 1",
		slug="product-1",
		description="Description 1",
	)
	product_2 = ProductFactory.build(
		id=_fixed_uuid(),
		category_id=category.id,
		title="Product 2",
		slug="product-2",
		description="Description 1",
	)

	sku_1 = Sku(
		id=_fixed_uuid(),
		product_id=product_1.id,
		name="Sku 1",
		price=100,
		active_quantity=1,
	)
	sku_2 = Sku(
		id=_fixed_uuid(),
		product_id=product_2.id,
		name="Sku 2",
		price=100,
		active_quantity=1,
	)

	db_session.add_all(
		[
			category,
			filter_1,
			filter_2,
			filter_value_1,
			filter_value_2,
			product_1,
			product_2,
			sku_1,
			sku_2,
		]
	)
	await db_session.commit()
	return CategoryWithProductsData(
		category=category,
		filters=(filter_1, filter_2),
		values=(filter_value_1, filter_value_2),
		products=(product_1, product_2),
	)


@dataclass(frozen=True, slots=True)
class VisibilityProductsData:
	category: Category
	visible_product: Product
	hidden_by_status_product: Product
	hidden_by_stock_product: Product


@pytest.fixture()
async def visibility_products(
	db_session: AsyncSession,
	category_with_products: CategoryWithProductsData,
) -> VisibilityProductsData:
	hidden_by_status = category_with_products.products[0]
	hidden_by_status.status = ProductStatusEnum.CREATED

	hidden_by_stock = category_with_products.products[1]
	existing_skus = (
		(
			await db_session.execute(
				select(Sku).where(Sku.product_id == hidden_by_stock.id)
			)
		)
		.scalars()
		.all()
	)
	for sku in existing_skus:
		sku.active_quantity = 0

	visible_product = ProductFactory.build(
		id=_fixed_uuid(),
		category_id=category_with_products.category.id,
		title="Visible product",
		slug="visible-product",
		description="Visible",
		status=ProductStatusEnum.MODERATED,
	)
	visible_sku = Sku(
		id=_fixed_uuid(),
		product_id=visible_product.id,
		name="Visible sku",
		price=100,
		active_quantity=1,
	)

	db_session.add_all([visible_product, visible_sku])
	await db_session.commit()

	return VisibilityProductsData(
		category=category_with_products.category,
		visible_product=visible_product,
		hidden_by_status_product=hidden_by_status,
		hidden_by_stock_product=hidden_by_stock,
	)
