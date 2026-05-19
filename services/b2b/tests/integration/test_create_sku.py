import pytest
from httpx import AsyncClient

from tests.integration.conftest import CategoryWithProductsData

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_first_sku_transitions_product_to_on_moderation(
	client: AsyncClient,
	product_no_skus: CategoryWithProductsData,
) -> None:
	response = await client.post(
		"/api/v1/skus",
		json={
			"product_id": str(product_no_skus.products[0].id),
			"name": "Test SKU",
			"price": 100,
			# image
		},
	)
	assert response.status_code == 201

	product_response = await client.get(
		f"/api/v1/products/{product_no_skus.products[0].id}",
	)
	assert product_response.status_code == 200
	assert product_response.json()["status"] == "ON_MODERATION"


async def test_second_sku_no_state_change(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
) -> None:
	response = await client.post(
		"/api/v1/skus",
		json={
			"product_id": str(category_with_products.products[0].id),
			"name": "Test SKU",
			"price": 100,
			# image
		},
	)
	assert response.status_code == 201

	product_response = await client.get(
		f"/api/v1/products/{category_with_products.products[0].id}",
	)
	assert product_response.status_code == 200
	assert product_response.json()["status"] == "MODERATED"


async def test_first_sku_emits_created_event_to_moderation(
	client: AsyncClient,
) -> None:
	pass


async def test_add_sku_to_hard_blocked_returns_403(
	client: AsyncClient, hard_blocked_product: CategoryWithProductsData
) -> None:
	response = await client.post(
		"/api/v1/skus",
		json={
			"product_id": str(hard_blocked_product.products[0].id),
			"name": "Test SKU",
			"price": 100,
			# image
		},
	)
	assert response.status_code == 403


async def test_missing_image_returns_400(
	client: AsyncClient, category_with_products: CategoryWithProductsData
) -> None:
	response = await client.post(
		"/api/v1/skus",
		json={
			"product_id": str(category_with_products.products[0].id),
			"name": "Test SKU",
			"price": 100,
		},
	)
	assert response.status_code == 400
