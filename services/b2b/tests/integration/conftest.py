from dataclasses import dataclass
import secrets

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import crud.session as session_crud
from core.security import create_access_token
from database.models.catalog.base import Category, ProductStatusEnum
from database.models.catalog.variants import Sku, Product
from database.models import Session
from database.models.identity.identity import Seller
from tests.factories.catalog import CategoryFactory, ProductFactory, SkuFactory

import uuid

from datetime import datetime, timezone, timedelta

from tests.factories.seller import SellerFactory


@dataclass(frozen=True, slots=True)
class CategoryWithProductsData:
	categories: list[Category]
	products: list[Product]
	skus: list[Sku]


@dataclass(frozen=True, slots=True)
class CreateProductData:
	seller: Seller
	category: Category


@pytest.fixture
async def create_product_data(db_session: AsyncSession) -> CreateProductData:
	seller: Seller = SellerFactory.build()

	db_session.add(seller)
	await db_session.commit()
	await db_session.refresh(seller)

	category = CategoryFactory.build()

	db_session.add(category)
	await db_session.commit()
	await db_session.refresh(category)

	return CreateProductData(seller=seller, category=category)


async def auth_headers(user_id: uuid.UUID, db: AsyncSession) -> dict:
	token = create_access_token(user_id)
	if not await session_crud.check_active_session(token, db):
		session = Session(
			user_id=user_id,
			access_token=token,
			refresh_token=secrets.token_hex(32),
			expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
		)
		await session_crud.add_session(session, db)

	return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
async def category_with_products(
	db_session: AsyncSession,
) -> CategoryWithProductsData:
	seller: Seller = SellerFactory.build()
	db_session.add(seller)
	await db_session.commit()
	await db_session.refresh(seller)

	categories = []
	products = []
	skus = []
	for _ in range(3):
		category = CategoryFactory.build()
		db_session.add(category)
		await db_session.commit()
		categories.append(category)
		for _ in range(3):
			product = ProductFactory.build(
				category_id=category.id,
				seller_id=seller.id,
				status=ProductStatusEnum.MODERATED,
			)
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
	seller: Seller = SellerFactory.build()
	db_session.add(seller)
	await db_session.commit()
	await db_session.refresh(seller)

	categories = []
	products = []
	skus = []
	for _ in range(3):
		category = CategoryFactory.build()
		db_session.add(category)
		await db_session.commit()
		categories.append(category)
		for _ in range(3):
			product = ProductFactory.build(
				category_id=category.id,
				seller_id=seller.id,
				status=ProductStatusEnum.CREATED,
			)
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
	seller: Seller = SellerFactory.build()
	db_session.add(seller)
	await db_session.commit()
	await db_session.refresh(seller)

	category = CategoryFactory.build()
	product = ProductFactory.build(
		category_id=category.id,
		seller_id=seller.id,
		status=ProductStatusEnum.HARD_BLOCKED,
	)
	sku = SkuFactory.build(product_id=product.id)
	db_session.add_all([category, product, sku])
	await db_session.commit()
	return CategoryWithProductsData([category], [product], [sku])
