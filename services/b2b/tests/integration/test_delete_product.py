import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import Product, ProductStatusEnum
from database.models.outbox import OutboxEvent, OutboxEventStatus
from crud.outbox import MODERATION_PRODUCT_DELETED, B2C_PRODUCT_DELETED
from tests.integration.conftest import (
	CategoryWithProductsData,
	EditProductData,
	auth_headers,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _moderation_outbox_events_for_product(
	db: AsyncSession, product_id: uuid.UUID
) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent).where(
			OutboxEvent.event_type == MODERATION_PRODUCT_DELETED,
			OutboxEvent.payload["product_id"].astext == str(product_id),
		)
	)
	return list(result.scalars().all())


async def _b2c_outbox_events_for_product(
	db: AsyncSession, product_id: uuid.UUID
) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent).where(
			OutboxEvent.event_type == B2C_PRODUCT_DELETED,
			OutboxEvent.payload["product_id"].astext == str(product_id),
		)
	)
	return list(result.scalars().all())


async def test_delete_sets_deleted_true(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = category_with_products.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	response = await client.delete(
		f"/api/v1/products/{product.id}",
		headers=headers,
	)

	assert response.status_code == 204

	updated_product = await db_session.get(Product, product.id)
	await db_session.refresh(updated_product)
	assert updated_product.deleted is True  # noqa
	assert updated_product.status == ProductStatusEnum.DELETED


async def test_delete_emits_event_to_moderation(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = category_with_products.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	response = await client.delete(
		f"/api/v1/products/{product.id}",
		headers=headers,
	)

	assert response.status_code == 204

	events = await _moderation_outbox_events_for_product(db_session, product.id)
	assert len(events) == 1
	assert events[0].payload["event"] == "DELETED"
	assert events[0].payload["seller_id"] == str(product.seller_id)
	assert events[0].status == OutboxEventStatus.PENDING


async def test_delete_emits_product_deleted_to_b2c(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = category_with_products.products[0]
	expected_sku_ids = [
		str(sku.id)
		for sku in category_with_products.skus
		if sku.product_id == product.id
	]
	headers = await auth_headers(product.seller_id, db_session)

	response = await client.delete(
		f"/api/v1/products/{product.id}",
		headers=headers,
	)

	assert response.status_code == 204

	events = await _b2c_outbox_events_for_product(db_session, product.id)
	assert len(events) == 1
	assert events[0].payload["event"] == "PRODUCT_DELETED"
	assert events[0].payload["product_id"] == str(product.id)
	assert events[0].status == OutboxEventStatus.PENDING
	assert set(events[0].payload["sku_ids"]) == set(expected_sku_ids)


async def test_delete_already_deleted_returns_404(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = category_with_products.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	response = await client.delete(
		f"/api/v1/products/{product.id}",
		headers=headers,
	)
	assert response.status_code == 204

	response = await client.delete(
		f"/api/v1/products/{product.id}",
		headers=headers,
	)
	assert response.status_code == 404


async def test_deleted_product_not_in_seller_list(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	db_session: AsyncSession,
) -> None:
	product = category_with_products.products[0]
	headers = await auth_headers(product.seller_id, db_session)

	response = await client.delete(
		f"/api/v1/products/{product.id}",
		headers=headers,
	)
	assert response.status_code == 204

	response = await client.get(
		"/api/v1/products/",
		headers=headers,
	)
	assert response.status_code == 200
	body = response.json()
	assert str(product.id) not in [product["id"] for product in body]


async def test_delete_product_no_auth_returns_401(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
) -> None:
	product = category_with_products.products[0]
	response = await client.delete(
		f"/api/v1/products/{product.id}",
	)
	assert response.status_code == 401


async def test_delete_others_product_returns_403(
	client: AsyncClient,
	edit_product_data: EditProductData,
	db_session: AsyncSession,
) -> None:
	product = edit_product_data.other_seller_product
	headers = await auth_headers(edit_product_data.owner.id, db_session)

	response = await client.delete(
		f"/api/v1/products/{product.id}",
		headers=headers,
	)
	assert response.status_code == 403
