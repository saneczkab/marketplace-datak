import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.variants import Sku
from tests.integration.conftest import (
	INVENTORY_SERVICE_KEY_HEADERS,
	FulfillInventoryData,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

FULFILL_URL = "/api/v1/inventory/fulfill"


async def _get_sku(db: AsyncSession, sku_id: uuid.UUID) -> Sku:
	result = await db.execute(
		select(Sku).where(Sku.id == sku_id).execution_options(populate_existing=True)
	)
	return result.scalar_one()


async def test_fulfill_decreases_reserved_and_stock_quantity(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
	db_session: AsyncSession,
) -> None:
	order_id = uuid.uuid4()
	response = await client.post(
		FULFILL_URL,
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"order_id": str(order_id),
			"items": [
				{"sku_id": str(fulfill_inventory_data.sku_a.id), "quantity": 2},
				{"sku_id": str(fulfill_inventory_data.sku_b.id), "quantity": 1},
			],
		},
	)
	assert response.status_code == 200
	body = response.json()
	assert body["order_id"] == str(order_id)
	assert body["status"] == "FULFILLED"
	assert body["processed_at"] is not None

	sku_a = await _get_sku(db_session, fulfill_inventory_data.sku_a.id)
	sku_b = await _get_sku(db_session, fulfill_inventory_data.sku_b.id)
	assert sku_a.reserved_quantity == 0
	assert sku_b.reserved_quantity == 0
	assert sku_a.stock_quantity == 8
	assert sku_b.stock_quantity == 4


async def test_active_quantity_unchanged(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		FULFILL_URL,
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"order_id": str(uuid.uuid4()),
			"items": [{"sku_id": str(fulfill_inventory_data.sku_a.id), "quantity": 2}],
		},
	)
	assert response.status_code == 200

	sku_a = await _get_sku(db_session, fulfill_inventory_data.sku_a.id)
	assert sku_a.active_quantity == 8
	assert sku_a.reserved_quantity == 0
	assert sku_a.stock_quantity == 8


async def test_idempotent_fulfill_no_double_deduction(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
	db_session: AsyncSession,
) -> None:
	order_id = uuid.uuid4()
	payload = {
		"order_id": str(order_id),
		"items": [{"sku_id": str(fulfill_inventory_data.sku_a.id), "quantity": 2}],
	}
	first = await client.post(
		FULFILL_URL, headers=INVENTORY_SERVICE_KEY_HEADERS, json=payload
	)
	second = await client.post(
		FULFILL_URL, headers=INVENTORY_SERVICE_KEY_HEADERS, json=payload
	)
	assert first.status_code == 200
	assert second.status_code == 200
	assert second.json()["status"] == "FULFILLED"

	sku_a = await _get_sku(db_session, fulfill_inventory_data.sku_a.id)
	assert sku_a.reserved_quantity == 0
	assert sku_a.active_quantity == 8
	assert sku_a.stock_quantity == 8


async def test_fulfill_exceeding_reserved_returns_409(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		FULFILL_URL,
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"order_id": str(uuid.uuid4()),
			"items": [{"sku_id": str(fulfill_inventory_data.sku_a.id), "quantity": 3}],
		},
	)
	assert response.status_code == 409
	assert response.json()["code"] == "CONFLICT"

	sku_a = await _get_sku(db_session, fulfill_inventory_data.sku_a.id)
	assert sku_a.reserved_quantity == 2
	assert sku_a.active_quantity == 8
	assert sku_a.stock_quantity == 10


async def test_missing_service_key_returns_401(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
) -> None:
	response = await client.post(
		FULFILL_URL,
		json={
			"order_id": str(uuid.uuid4()),
			"items": [{"sku_id": str(fulfill_inventory_data.sku_a.id), "quantity": 2}],
		},
	)
	assert response.status_code == 401
	assert response.json()["code"] == "UNAUTHORIZED"
