import pytest
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product, ProductBlockReason
from database.models.catalog.base import Category

from tests.factories.catalog import (
	CategoryFactory,
	ProductFactory,
	BlockingReasonFactory,
)


@dataclass(frozen=True, slots=True)
class BlockingProduct:
	product: Product
	reason: ProductBlockReason


@pytest.fixture()
async def product_with_block(db_session: AsyncSession) -> BlockingProduct:
	category: Category = CategoryFactory.build()
	db_session.add(category)
	await db_session.commit()
	await db_session.refresh(category)

	product: Product = ProductFactory.build(category_id=category.id)

	db_session.add(product)
	await db_session.commit()
	await db_session.refresh(product)

	reason: ProductBlockReason = BlockingReasonFactory.build()

	db_session.add(reason)
	await db_session.commit()
	await db_session.refresh(reason)

	return BlockingProduct(product, reason)
