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


async def _get_sku(db: AsyncSession, sku_id: uuid.UUID) -> Sku:
	result = await db.execute(
		select(Sku).where(Sku.id == sku_id).execution_options(populate_existing=True)
	)
	return result.scalar_one()


async def test_fulfill_decreases_reserved_quantity(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		"/api/v1/fulfill",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"order_id": str(uuid.uuid4()),
			"items": [
				{"sku_id": str(fulfill_inventory_data.sku_a.id), "quantity": 2},
				{"sku_id": str(fulfill_inventory_data.sku_b.id), "quantity": 1},
			],
		},
	)
	assert response.status_code == 200
	assert response.json() == {"ok": True}

	sku_a = await _get_sku(db_session, fulfill_inventory_data.sku_a.id)
	sku_b = await _get_sku(db_session, fulfill_inventory_data.sku_b.id)
	assert sku_a.reserved_quantity == 0
	assert sku_b.reserved_quantity == 0


async def test_active_quantity_unchanged(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		"/api/v1/fulfill",
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
		"/api/v1/fulfill", headers=INVENTORY_SERVICE_KEY_HEADERS, json=payload
	)
	second = await client.post(
		"/api/v1/fulfill", headers=INVENTORY_SERVICE_KEY_HEADERS, json=payload
	)
	assert first.status_code == 200
	assert second.status_code == 200

	sku_a = await _get_sku(db_session, fulfill_inventory_data.sku_a.id)
	assert sku_a.reserved_quantity == 0
	assert sku_a.active_quantity == 8


async def test_missing_service_key_returns_401(
	client: AsyncClient,
	fulfill_inventory_data: FulfillInventoryData,
) -> None:
	response = await client.post(
		"/api/v1/fulfill",
		json={
			"order_id": str(uuid.uuid4()),
			"items": [{"sku_id": str(fulfill_inventory_data.sku_a.id), "quantity": 2}],
		},
	)
	assert response.status_code == 401
	assert response.json()["code"] == "UNAUTHORIZED"
