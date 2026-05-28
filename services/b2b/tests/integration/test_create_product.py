import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import (
	CategoryWithProductsData,
	CreateProductData,
	auth_headers,
)


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_product_returns_201_with_created_status(
	client: AsyncClient,
	create_product_data: CreateProductData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		"/api/v1/products/",
		headers=await auth_headers(create_product_data.seller.id, db_session),
		json={
			"category_id": str(create_product_data.category.id),
			"title": "Test product",
			"description": "Some smart words",
			"slug": "some-product",
		},
	)

	assert response.status_code == 201


async def test_seller_id_taken_from_jwt(
	client: AsyncClient,
	create_product_data: CreateProductData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		"/api/v1/products/",
		headers=await auth_headers(create_product_data.seller.id, db_session),
		json={
			"category_id": str(create_product_data.category.id),
			"title": "Test product",
			"description": "Some smart words",
			"slug": "some-product",
		},
	)

	assert response.json()["seller_id"] == str(create_product_data.seller.id)


async def test_missing_images_returns_400(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
) -> None:
	response = await client.post(
		"/api/v1/products/",
		json={
			"category_id": str(category_with_products.categories[0].id),
			"title": "Test Product",
			"description": "Test Description",
			"slug": "test-product",
		},
	)
	assert response.status_code == 400


async def test_missing_category_returns_422(
	client: AsyncClient,
	create_product_data: CreateProductData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		"/api/v1/products/",
		headers=await auth_headers(create_product_data.seller.id, db_session),
		json={
			"title": "Test product",
			"description": "Some smart words",
			"slug": "some-product",
		},
	)

	assert response.status_code == 422
