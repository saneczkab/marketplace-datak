import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import CategoryWithProductsData, auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_sku(client: AsyncClient, headers: dict, product_id: str) -> dict:
	response = await client.post(
		"/api/v1/skus",
		headers=headers,
		json={"product_id": product_id, "name": "Test SKU", "price": 100},
	)
	assert response.status_code == 201
	return response.json()


async def _attach_sku_image(client: AsyncClient, headers: dict, sku_id: str) -> None:
	response = await client.post(
		f"/api/v1/skus/{sku_id}/images",
		headers=headers,
		json={"url": "/s3/test-sku.jpg", "ordering": 0},
	)
	assert response.status_code == 201


async def test_first_sku_transitions_product_to_on_moderation(
	client: AsyncClient,
	product_no_skus: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = product_no_skus.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	sku = await _create_sku(client, headers, str(product.id))
	await _attach_sku_image(client, headers, sku["id"])

	product_response = await client.get(
		f"/api/v1/products/{product.id}",
		headers=headers,
		params={"seller_id": str(product.seller_id)},
	)
	assert product_response.status_code == 200
	assert product_response.json()["status"] == "ON_MODERATION"


async def test_second_sku_no_state_change(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = category_with_products.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	await _create_sku(client, headers, str(product.id))

	product_response = await client.get(
		f"/api/v1/products/{product.id}",
		headers=headers,
		params={"seller_id": str(product.seller_id)},
	)
	assert product_response.status_code == 200
	assert product_response.json()["status"] == "MODERATED"


async def test_add_sku_to_hard_blocked_returns_403(
	client: AsyncClient,
	hard_blocked_product: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = hard_blocked_product.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	response = await client.post(
		"/api/v1/skus",
		headers=headers,
		json={"product_id": str(product.id), "name": "Test SKU", "price": 100},
	)
	assert response.status_code == 403


async def test_missing_image_returns_400(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = category_with_products.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	sku = await _create_sku(client, headers, str(product.id))

	response = await client.post(
		f"/api/v1/skus/{sku['id']}/images",
		headers=headers,
		json={"ordering": 0},
	)
	assert response.status_code == 400
