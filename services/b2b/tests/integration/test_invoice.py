import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import (
	CategoryWithProductsData,
	EditProductData,
	auth_headers,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_invoice_with_moderated_sku_returns_201(
	client: AsyncClient,
	edit_product_data: EditProductData,
	db_session: AsyncSession,
) -> None:
	data = edit_product_data
	headers = await auth_headers(data.owner.id, db_session)

	response = await client.post(
		"/api/v1/invoices",
		headers=headers,
		json={
			"items": [
				{"sku_id": str(data.moderated_sku.id), "quantity": 10},
			],
		},
	)

	assert response.status_code == 201
	body = response.json()
	assert body["status"] == "CREATED"
	assert body["seller_id"] == str(data.owner.id)
	assert len(body["items"]) == 1
	assert body["items"][0]["sku_id"] == str(data.moderated_sku.id)
	assert body["items"][0]["quantity"] == 10


async def test_empty_items_returns_400(
	client: AsyncClient,
	edit_product_data: EditProductData,
	db_session: AsyncSession,
) -> None:
	headers = await auth_headers(edit_product_data.owner.id, db_session)

	response = await client.post(
		"/api/v1/invoices",
		headers=headers,
		json={"items": []},
	)

	assert response.status_code == 400
	body = response.json()
	assert body["code"] == "INVALID_REQUEST"
	assert body["message"] == "At least one item is required"


async def test_non_moderated_sku_returns_400(
	client: AsyncClient,
	product_on_moderation_with_one_sku: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	seller_id = product_on_moderation_with_one_sku.products[0].seller_id
	sku_id = product_on_moderation_with_one_sku.skus[0].id
	headers = await auth_headers(seller_id, db_session)

	response = await client.post(
		"/api/v1/invoices",
		headers=headers,
		json={"items": [{"sku_id": str(sku_id), "quantity": 5}]},
	)

	assert response.status_code == 400
	body = response.json()
	assert body["code"] == "INVALID_REQUEST"
	assert body["message"] == "Invoice can only be created for MODERATED products"


async def test_others_sku_returns_403(
	client: AsyncClient,
	edit_product_data: EditProductData,
	db_session: AsyncSession,
) -> None:
	headers = await auth_headers(edit_product_data.owner.id, db_session)

	response = await client.post(
		"/api/v1/invoices",
		headers=headers,
		json={
			"items": [
				{"sku_id": str(edit_product_data.other_seller_sku.id), "quantity": 3},
			],
		},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["code"] == "NOT_OWNER"
	assert (
		body["message"] == "One or more SKUs do not belong to the authenticated seller"
	)
