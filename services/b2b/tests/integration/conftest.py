import uuid
from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import Category
from database.models.catalog.variants import Sku, Product
from tests.factories.catalog import CategoryFactory, ProductFactory, SkuFactory


def _fixed_uuid() -> uuid.UUID:
	return uuid.uuid4()


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
