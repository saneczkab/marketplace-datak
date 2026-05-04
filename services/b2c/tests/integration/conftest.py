import uuid

import pytest
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


@pytest.fixture()
def uuids() -> dict[str, uuid.UUID]:
	"""
	UUIDs for test data.
	"""
	return {
		"root": uuid.uuid4(),
		"child": uuid.uuid4(),
		"grandchild": uuid.uuid4(),
		"orphan": uuid.uuid4(),
		"missing_parent": uuid.uuid4(),
		"category_with_filters": uuid.uuid4(),
		"filter_1": uuid.uuid4(),
		"filter_2": uuid.uuid4(),
		"filter_value_1": uuid.uuid4(),
		"filter_value_2": uuid.uuid4(),
		"product_1": uuid.uuid4(),
		"product_2": uuid.uuid4(),
	}


@pytest.fixture()
async def categories_tree(
	db_session: AsyncSession, uuids: dict[str, uuid.UUID]
) -> dict[str, uuid.UUID]:
	"""
	Create categories tree test data.
	"""
	db_session.add_all(
		[
			Category(
				id=uuids["root"], parent_id=None, name="Электроника", slug="electronics"
			),
			Category(
				id=uuids["child"],
				parent_id=uuids["root"],
				name="Смартфоны",
				slug="smartphones",
			),
			Category(
				id=uuids["grandchild"],
				parent_id=uuids["child"],
				name="Android",
				slug="android",
			),
		]
	)
	await db_session.commit()
	return uuids


@pytest.fixture()
async def orphan_category(
	db_session: AsyncSession, uuids: dict[str, uuid.UUID]
) -> dict[str, uuid.UUID]:
	"""
	Create orphan category test data.
	Sets session replication role to replica to avoid foreign key constraints errors. Needs for orphan category.
	"""
	await db_session.execute(text("SET session_replication_role = replica"))
	db_session.add(
		Category(
			id=uuids["orphan"],
			parent_id=uuids["missing_parent"],
			name="Orphan",
			slug="orphan",
		)
	)
	await db_session.commit()
	await db_session.execute(text("SET session_replication_role = DEFAULT"))
	await db_session.commit()
	return uuids


@pytest.fixture()
async def category_with_products(
	db_session: AsyncSession, uuids: dict[str, uuid.UUID]
) -> dict[str, uuid.UUID]:
	"""
	Create category with filters test data.
	"""
	db_session.add(
		Category(
			id=uuids["category_with_filters"],
			name="Category with Filters",
			slug="category-with-filters",
		)
	)
	db_session.add(
		CategoryFilters(
			id=uuids["filter_1"],
			category_id=uuids["category_with_filters"],
			name="Filter 1",
			slug="filter-1",
			type=FilterTypeEnum.LIST,
			value="Value 1",
		),
	)
	db_session.add(
		CategoryFilters(
			id=uuids["filter_2"],
			category_id=uuids["category_with_filters"],
			name="Filter 2",
			slug="filter-2",
			type=FilterTypeEnum.LIST,
			value="Value 2",
		)
	)
	db_session.add(
		FilterValues(
			id=uuids["filter_value_1"],
			filter_id=uuids["filter_1"],
			value="Value 1",
		)
	)
	db_session.add(
		FilterValues(
			id=uuids["filter_value_2"],
			filter_id=uuids["filter_2"],
			value="Value 2",
		)
	)
	db_session.add(
		Product(
			id=uuids["product_1"],
			category_id=uuids["category_with_filters"],
			title="Product 1",
			slug="product-1",
			description="Description 1",
			status=ProductStatusEnum.CREATED,
		)
	)
	db_session.add(
		Product(
			id=uuids["product_2"],
			category_id=uuids["category_with_filters"],
			title="Product 2",
			slug="product-2",
			description="Description 1",
			status=ProductStatusEnum.CREATED,
		)
	)
	await db_session.commit()
	return uuids
