import uuid
import pytest
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product, ProductBlockReason, User, Category, Sku, CartItem

from tests.factories.cart import CartItemFactory
from tests.factories.catalog import (
	CategoryFactory,
	ProductFactory,
	BlockingReasonFactory,
	SkuFactory,
)
from tests.factories.user import UserFactory


@dataclass(frozen=True, slots=True)
class BlockingProduct:
	product: Product
	reason: ProductBlockReason
	idempotency_key: uuid.UUID


@dataclass(frozen=True, slots=True)
class BlockingProductInCart:
	product: Product
	sku: Sku
	reason: ProductBlockReason
	idempotency_key: uuid.UUID
	user: User
	cart_item: CartItem


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

	return BlockingProduct(product, reason, uuid.uuid4())


@pytest.fixture()
async def product_in_cart_with_block(db_session: AsyncSession) -> BlockingProductInCart:
	category: Category = CategoryFactory.build()
	db_session.add(category)
	await db_session.commit()
	await db_session.refresh(category)

	product: Product = ProductFactory.build(category_id=category.id)

	db_session.add(product)
	await db_session.commit()
	await db_session.refresh(product)

	sku: Sku = SkuFactory.build(product_id=product.id)

	db_session.add(sku)
	await db_session.commit()
	await db_session.refresh(sku)

	reason: ProductBlockReason = BlockingReasonFactory.build()

	db_session.add(reason)
	await db_session.commit()
	await db_session.refresh(reason)

	user: User = UserFactory.build()

	db_session.add(user)
	await db_session.commit()
	await db_session.refresh(user)

	cart_item: CartItem = CartItemFactory.build(sku_id=sku.id, user_id=user.id)

	db_session.add(cart_item)
	await db_session.commit()
	await db_session.refresh(cart_item)

	return BlockingProductInCart(
		product=product,
		sku=sku,
		reason=reason,
		idempotency_key=uuid.uuid4(),
		user=user,
		cart_item=cart_item,
	)
