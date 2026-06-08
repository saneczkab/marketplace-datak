import pytest
from httpx import AsyncClient

from tests.integration.catalog.conftest import ProductData


pytestmark = pytest.mark.asyncio(loop_scope="session")

PRODUCT_DETAIL_URL = "/api/v1/catalog/products/{product_id}"


async def test_product_card_returns_full_data_with_skus(
	client: AsyncClient,
	products_data: ProductData,
) -> None:
	product = products_data.base_product
	skus = products_data.skus
	response = await client.get(PRODUCT_DETAIL_URL.format(product_id=product.id))

	assert response.status_code == 200
	body = response.json()
	assert body["id"] == str(product.id)
	assert body["name"] == product.title
	assert body["slug"] == product.slug
	assert body["description"] == product.description
	assert body["has_stock"] is True
	assert len(body["images"]) == 1
	assert body["images"][0]["url"] == "https://cdn.example.com/product.jpg"
	assert body["images"][0]["ordering"] == 0

	response_skus = body["skus"]
	assert [item["name"] for item in response_skus] == [sku.name for sku in skus]
	assert response_skus[0]["price"] == 9000
	assert response_skus[0]["old_price"] == 10000
	assert response_skus[0]["available_quantity"] == 3
	assert response_skus[0]["images"][0]["url"] == "https://cdn.example.com/sku1.jpg"
	assert response_skus[1]["price"] == 20000
	assert response_skus[1]["old_price"] is None
	assert response_skus[1]["available_quantity"] == 1


async def test_blocked_product_returns_404(
	client: AsyncClient,
	blocked_product_data: ProductData,
) -> None:
	product = blocked_product_data.base_product
	response = await client.get(PRODUCT_DETAIL_URL.format(product_id=product.id))
	assert response.status_code == 404


async def test_deleted_product_returns_404(
	client: AsyncClient,
	deleted_product_data: ProductData,
) -> None:
	product = deleted_product_data.base_product
	response = await client.get(PRODUCT_DETAIL_URL.format(product_id=product.id))
	assert response.status_code == 404


async def test_sku_without_stock_is_shown_as_unavailable(
	client: AsyncClient,
	product_skus_out_of_stock_data: ProductData,
) -> None:
	product = product_skus_out_of_stock_data.base_product
	response = await client.get(PRODUCT_DETAIL_URL.format(product_id=product.id))

	assert response.status_code == 200
	body = response.json()
	assert body["id"] == str(product.id)
	assert body["has_stock"] is False
	assert body["skus"][0]["available_quantity"] == 0


async def test_cost_price_absent_in_response(
	client: AsyncClient,
	products_data: ProductData,
) -> None:
	product = products_data.base_product
	response = await client.get(PRODUCT_DETAIL_URL.format(product_id=product.id))

	assert response.status_code == 200
	body = response.json()
	assert len(body["skus"]) > 0
	for sku in body["skus"]:
		assert "cost_price" not in sku
		assert "reserved_quantity" not in sku
		assert "active_quantity" not in sku
		assert "discount" not in sku
