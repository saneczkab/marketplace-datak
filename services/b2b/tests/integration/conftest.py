from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import Category, ProductStatusEnum
from database.models.catalog.variants import Sku, Product
from tests.factories.catalog import CategoryFactory, ProductFactory, SkuFactory


@dataclass(frozen=True, slots=True)
class CategoryWithProductsData:
	categories: list[Category]
	products: list[Product]
	skus: list[Sku]


@pytest.fixture()
async def category_with_products(
	db_session: AsyncSession,
) -> CategoryWithProductsData:
	categories = []
	products = []
	skus = []
	for _ in range(3):
		category = CategoryFactory.build()
		db_session.add(category)
		await db_session.commit()
		categories.append(category)
		for _ in range(3):
			product = ProductFactory.build(category_id=category.id)
			db_session.add(product)
			await db_session.commit()
			products.append(product)
			for _ in range(3):
				sku = SkuFactory.build(product_id=product.id)
				db_session.add(sku)
				await db_session.commit()
				skus.append(sku)

	db_session.add_all([*categories, *products, *skus])
	await db_session.commit()
	return CategoryWithProductsData(categories, products, skus)


@pytest.fixture()
async def product_no_skus(
	db_session: AsyncSession,
) -> CategoryWithProductsData:
	categories = []
	products = []
	skus = []
	for _ in range(3):
		category = CategoryFactory.build()
		db_session.add(category)
		await db_session.commit()
		categories.append(category)
		for _ in range(3):
			product = ProductFactory.build(category_id=category.id)
			db_session.add(product)
			await db_session.commit()
			products.append(product)
		db_session.add_all([*categories, *products])
	await db_session.commit()
	return CategoryWithProductsData(categories, products, skus)

@pytest.fixture()
async def hard_blocked_product(
	db_session: AsyncSession,
) -> CategoryWithProductsData:
    category = CategoryFactory.build()
    product = ProductFactory.build(category_id=category.id, status=ProductStatusEnum.BLOCKED)
    sku = SkuFactory.build(product_id=product.id)
    db_session.add_all([category, product, sku])
    await db_session.commit()
    return CategoryWithProductsData([category], [product], [sku])