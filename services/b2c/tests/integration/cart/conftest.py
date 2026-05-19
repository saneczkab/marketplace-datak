import uuid
from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import crud.session as session_crud
from core.security import create_access_token
from database.models import Category, Product, ProductStatusEnum, Sku
from database.models.cart.item import CartItem
from database.models.identity.user import User
from database.models.personal.profile import Favorite, Subscription
from database.models.storefront.main import Collection, CollectionProduct
from tests.factories.catalog import (
	CartItemFactory,
	CategoryFactory,
	ProductFactory,
	SkuFactory,
)
from tests.factories.user import UserFactory
from tests.factories.cart import (
	CollectionFactory,
	CollectionProductFactory,
	FavoriteFactory,
	SubscriptionFactory,
)


async def auth_headers(user_id: uuid.UUID, db: AsyncSession) -> dict[str, str]:
	token = create_access_token(user_id)
	if not await session_crud.check_active_session(token, db):
		await session_crud.create_session(user_id, token, str(uuid.uuid4()), db)
	return {"Authorization": f"Bearer {token}"}


@dataclass(frozen=True, slots=True)
class FavoritesData:
	user: User
	categories: list[Category]
	products: list[Product]
	skus: list[Sku]
	favorites: list[Favorite | None]
	subscriptions: list[Subscription | None]


@pytest.fixture()
async def empty_favorites_data(db_session: AsyncSession) -> FavoritesData:
	user = UserFactory.build()
	category = CategoryFactory.build()
	product = ProductFactory.build(category_id=category.id)
	sku = SkuFactory.build(product_id=product.id)
	subscription = SubscriptionFactory.build(user_id=user.id, product_id=product.id)
	db_session.add_all([user, category, product, sku, subscription])
	await db_session.commit()
	return FavoritesData(
		user=user,
		categories=[category],
		products=[product],
		skus=[sku],
		favorites=[None],
		subscriptions=[subscription],
	)


@pytest.fixture()
async def favorites_data(db_session: AsyncSession) -> FavoritesData:
	user = UserFactory.build()
	category = CategoryFactory.build()
	product = ProductFactory.build(category_id=category.id)
	sku = SkuFactory.build(product_id=product.id)
	product_blocked = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.BLOCKED,
	)
	sku_blocked = SkuFactory.build(product_id=product_blocked.id)
	subscription = SubscriptionFactory.build(user_id=user.id, product_id=product.id)
	favorite = FavoriteFactory.build(user_id=user.id, product_id=product.id)
	favorite_blocked = FavoriteFactory.build(
		user_id=user.id, product_id=product_blocked.id
	)
	db_session.add_all(
		[
			user,
			category,
			product,
			sku,
			product_blocked,
			sku_blocked,
			subscription,
			favorite,
			favorite_blocked,
		]
	)
	await db_session.commit()
	return FavoritesData(
		user=user,
		categories=[category, category],
		products=[product, product_blocked],
		skus=[sku, sku_blocked],
		favorites=[favorite, favorite_blocked],
		subscriptions=[subscription, None],
	)


@dataclass(frozen=True, slots=True)
class SubscriptionsData:
	user: User
	product: Product
	subscription: Subscription | None


@pytest.fixture()
async def empty_subscriptions_data(db_session: AsyncSession) -> SubscriptionsData:
	user = UserFactory.build()
	category = CategoryFactory.build()
	product = ProductFactory.build(category_id=category.id)
	db_session.add_all([user, category, product])
	await db_session.commit()
	return SubscriptionsData(
		user=user,
		product=product,
		subscription=None,
	)


@pytest.fixture()
async def subscriptions_data(db_session: AsyncSession) -> SubscriptionsData:
	user = UserFactory.build()
	category = CategoryFactory.build()
	product = ProductFactory.build(category_id=category.id)
	subscription = SubscriptionFactory.build(user_id=user.id, product_id=product.id)
	db_session.add_all([user, category, product, subscription])
	await db_session.commit()
	return SubscriptionsData(
		user=user,
		product=product,
		subscription=subscription,
	)


@dataclass(frozen=True, slots=True)
class CartData:
	user: User
	categories: list[Category]
	products: list[Product]
	skus: list[Sku]
	items: list[CartItem | None]


@pytest.fixture()
async def cart_data(db_session: AsyncSession) -> CartData:
	user = UserFactory.build()
	category = CategoryFactory.build()
	products = [ProductFactory.build(category_id=category.id) for _ in range(3)]
	skus = [SkuFactory.build(product_id=product.id) for product in products]
	items = [CartItemFactory.build(user_id=user.id, sku_id=sku.id) for sku in skus]
	db_session.add_all([user, category, *products, *skus, *items])
	await db_session.commit()
	return CartData(
		user=user,
		categories=[category],
		products=products,
		skus=skus,
		items=items,
	)


@dataclass(frozen=True, slots=True)
class CollectionsData:
	categories: list[Category]
	products: list[Product]
	skus: list[Sku]
	collections: list[Collection]
	collection_products: list[CollectionProduct]


@pytest.fixture()
async def collections_data(db_session: AsyncSession) -> CollectionsData:
	category = CategoryFactory.build()
	products = [ProductFactory.build(category_id=category.id) for _ in range(3)]
	product_blocked = ProductFactory.build(
		category_id=category.id, status=ProductStatusEnum.BLOCKED
	)
	products.append(product_blocked)
	skus = [SkuFactory.build(product_id=product.id) for product in products]
	collections = [CollectionFactory.build() for _ in range(3)]
	collection_products = [
		CollectionProductFactory.build(
			product_id=product.id, collection_id=collection.id
		)
		for product in products
		for collection in collections
	]
	db_session.add_all([category, *products, *skus, *collections, *collection_products])
	await db_session.commit()
	return CollectionsData(
		categories=[category],
		products=products,
		skus=skus,
		collections=collections,
		collection_products=collection_products,
	)
