from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession


import pytest
from database.models import Category, Product, ProductStatusEnum, Sku
from database.models.identity.user import User
from database.models.personal.profile import Favorite, Subscription
from tests.factories.catalog import CategoryFactory, ProductFactory, SkuFactory
from tests.factories.user import UserFactory
from tests.factories.cart import FavoriteFactory, SubscriptionFactory


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
		]
	)
	await db_session.commit()
	return FavoritesData(
		user=user,
		categories=[category, category],
		products=[product, product_blocked],
		skus=[sku, sku_blocked],
		favorites=[favorite, None],
		subscriptions=[subscription, None],
	)
