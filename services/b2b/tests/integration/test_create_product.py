import pytest
from httpx import AsyncClient

from tests.integration.conftest import CategoryWithProductsData, auth_headers


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_product_returns_201_with_created_status(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,  # noqa
) -> None:
	response = await client.post("/api/v1/products", headers=await auth_headers())  # noqa


async def test_seller_id_taken_from_jwt(
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
	assert response.status_code == 201
	assert response.json()["seller_id"] == "00000000-0000-0000-0000-000000000000"


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


async def missing_category_returns_400(
	client: AsyncClient,
) -> None:
	response = await client.post(
		"/api/v1/products/",
		json={
			"title": "Test Product",
			"description": "Test Description",
			"slug": "test-product",
		},
	)
	assert response.status_code == 400
