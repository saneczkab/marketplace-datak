import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import CategoryWithProductsData, auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_sku(
	client: AsyncClient,
	headers: dict,
	product_id: str,
	with_images: bool = False,
) -> dict:
	body = {"product_id": product_id, "name": "Test SKU", "price": 100}
	if with_images:
		body["images"] = [{"url": "/s3/test-sku.jpg", "ordering": 0}]
	response = await client.post("/api/v1/skus", headers=headers, json=body)
	assert response.status_code == 201
	return response.json()


async def test_first_sku_emits_created_event_to_moderation(
	client: AsyncClient,
	product_no_skus: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = product_no_skus.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	sku = await _create_sku(client, headers, str(product.id), with_images=True)
	assert len(sku["images"]) == 1
	assert sku["images"][0]["url"] == "/s3/test-sku.jpg"

	product_response = await client.get(
		f"/api/v1/products/{product.id}",
		headers=headers,
		params={"seller_id": str(product.seller_id)},
	)
	assert product_response.status_code == 200
	assert product_response.json()["status"] == "ON_MODERATION"


async def test_first_sku_enqueues_created_event_to_outbox(
	client: AsyncClient,
	product_no_skus: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	from sqlalchemy import select

	from database.models.outbox import OutboxEvent, OutboxEventStatus

	product = product_no_skus.products[1]
	headers = await auth_headers(product.seller_id, db_session)

	await _create_sku(client, headers, str(product.id), with_images=True)

	result = await db_session.execute(
		select(OutboxEvent).where(
			OutboxEvent.payload["product_id"].astext == str(product.id)
		)
	)
	events = list(result.scalars().all())
	assert len(events) == 1
	assert events[0].payload["event"] == "CREATED"
	assert events[0].payload["seller_id"] == str(product.seller_id)
	assert events[0].status == OutboxEventStatus.PENDING


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


async def test_first_sku_without_images_returns_400(
	client: AsyncClient,
	product_no_skus: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = product_no_skus.products[2]
	headers = await auth_headers(product.seller_id, db_session)

	response = await client.post(
		"/api/v1/skus",
		headers=headers,
		json={"product_id": str(product.id), "name": "Test SKU", "price": 100},
	)
	assert response.status_code == 400


async def test_missing_image_url_on_attach_returns_400(
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
