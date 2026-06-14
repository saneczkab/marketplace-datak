import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.outbox import MODERATION_PRODUCT_DELETED, B2C_SKU_OUT_OF_STOCK
from database.models.catalog.base import Product, ProductStatusEnum
from database.models.catalog.variants import Sku
from database.models.outbox import OutboxEvent
from tests.integration.conftest import DeleteSkuData, auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _sku_exists(db: AsyncSession, sku_id: uuid.UUID) -> bool:
	result = await db.execute(select(Sku.id).where(Sku.id == sku_id))
	return result.scalar_one_or_none() is not None


async def _moderation_deleted_events(
	db: AsyncSession, product_id: uuid.UUID
) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent).where(
			OutboxEvent.event_type == MODERATION_PRODUCT_DELETED,
			OutboxEvent.payload["product_id"].astext == str(product_id),
		)
	)
	return list(result.scalars().all())


async def _sku_out_of_stock_events(
	db: AsyncSession, sku_id: uuid.UUID
) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent).where(
			OutboxEvent.event_type == B2C_SKU_OUT_OF_STOCK,
			OutboxEvent.payload["payload"]["sku_id"].astext == str(sku_id),
		)
	)
	return list(result.scalars().all())


async def test_delete_sku_succeeds(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
	db_session: AsyncSession,
) -> None:
	sku = delete_sku_data.happy_sku
	headers = await auth_headers(delete_sku_data.seller.id, db_session)

	response = await client.delete(f"/api/v1/skus/{sku.id}", headers=headers)

	assert response.status_code == 204
	assert await _sku_exists(db_session, sku.id) is False


async def test_delete_sku_with_active_reserves_returns_409(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
	db_session: AsyncSession,
) -> None:
	sku = delete_sku_data.reserved_sku
	headers = await auth_headers(delete_sku_data.seller.id, db_session)

	response = await client.delete(f"/api/v1/skus/{sku.id}", headers=headers)

	assert response.status_code == 409
	assert response.json()["code"] == "CONFLICT"
	assert await _sku_exists(db_session, sku.id) is True


async def test_last_sku_on_moderation_transitions_product_to_created(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
	db_session: AsyncSession,
) -> None:
	product = delete_sku_data.on_moderation_product
	sku = delete_sku_data.on_moderation_sku
	headers = await auth_headers(delete_sku_data.seller.id, db_session)

	response = await client.delete(f"/api/v1/skus/{sku.id}", headers=headers)

	assert response.status_code == 204

	refreshed = await db_session.get(Product, product.id)
	await db_session.refresh(refreshed)
	assert refreshed.status == ProductStatusEnum.CREATED

	events = await _moderation_deleted_events(db_session, product.id)
	assert len(events) == 1
	assert events[0].payload["event"] == "DELETED"
	assert events[0].payload["seller_id"] == str(delete_sku_data.seller.id)


async def test_delete_sku_hard_blocked_product_returns_403(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
	db_session: AsyncSession,
) -> None:
	sku = delete_sku_data.hard_blocked_sku
	headers = await auth_headers(delete_sku_data.seller.id, db_session)

	response = await client.delete(f"/api/v1/skus/{sku.id}", headers=headers)

	assert response.status_code == 403
	assert response.json()["code"] == "FORBIDDEN"
	assert await _sku_exists(db_session, sku.id) is True


async def test_sku_out_of_stock_event_on_moderated_product(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
	db_session: AsyncSession,
) -> None:
	sku = delete_sku_data.out_of_stock_sku
	headers = await auth_headers(delete_sku_data.seller.id, db_session)

	response = await client.delete(f"/api/v1/skus/{sku.id}", headers=headers)

	assert response.status_code == 204

	events = await _sku_out_of_stock_events(db_session, sku.id)
	assert len(events) == 1
	assert events[0].payload["event_type"] == "SKU_OUT_OF_STOCK"
	assert events[0].payload["payload"]["product_id"] == str(
		delete_sku_data.out_of_stock_product.id
	)


async def test_delete_sku_not_owner_returns_403(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
	db_session: AsyncSession,
) -> None:
	sku = delete_sku_data.happy_sku
	headers = await auth_headers(delete_sku_data.other_seller.id, db_session)

	response = await client.delete(f"/api/v1/skus/{sku.id}", headers=headers)

	assert response.status_code == 403
	assert response.json()["code"] == "NOT_OWNER"


async def test_delete_sku_not_found_returns_404(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
	db_session: AsyncSession,
) -> None:
	headers = await auth_headers(delete_sku_data.seller.id, db_session)

	response = await client.delete(f"/api/v1/skus/{uuid.uuid4()}", headers=headers)

	assert response.status_code == 404
	assert response.json()["code"] == "NOT_FOUND"


async def test_delete_sku_no_auth_returns_401(
	client: AsyncClient,
	delete_sku_data: DeleteSkuData,
) -> None:
	sku = delete_sku_data.happy_sku
	response = await client.delete(f"/api/v1/skus/{sku.id}")
	assert response.status_code == 401
