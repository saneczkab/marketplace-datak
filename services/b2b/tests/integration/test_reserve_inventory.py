import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.variants import Sku
from database.models.event.outbox import OutboxEvent
from tests.integration.conftest import (
	INVENTORY_SERVICE_KEY_HEADERS,
	ReserveInventoryData,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _get_sku(db: AsyncSession, sku_id: uuid.UUID) -> Sku:
	result = await db.execute(
		select(Sku).where(Sku.id == sku_id).execution_options(populate_existing=True)
	)
	return result.scalar_one()


async def _outbox_sku_out_of_stock_events(
	db: AsyncSession, sku_id: uuid.UUID
) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent).where(OutboxEvent.event_type == "SKU_OUT_OF_STOCK")
	)
	return [
		event
		for event in result.scalars().all()
		if event.payload.get("payload", {}).get("sku_id") == str(sku_id)
	]


async def test_reserve_all_skus_succeeds(
	client: AsyncClient,
	reserve_inventory_data: ReserveInventoryData,
	db_session: AsyncSession,
) -> None:
	order_id = uuid.uuid4()
	idempotency_key = uuid.uuid4()
	response = await client.post(
		"/api/v1/inventory/reserve",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"idempotency_key": str(idempotency_key),
			"order_id": str(order_id),
			"items": [
				{"sku_id": str(reserve_inventory_data.sku_a.id), "quantity": 2},
				{"sku_id": str(reserve_inventory_data.sku_b.id), "quantity": 1},
			],
		},
	)
	assert response.status_code == 200
	body = response.json()
	assert body["order_id"] == str(order_id)
	assert body["status"] == "RESERVED"
	assert "reserved_at" in body

	sku_a = await _get_sku(db_session, reserve_inventory_data.sku_a.id)
	sku_b = await _get_sku(db_session, reserve_inventory_data.sku_b.id)
	assert sku_a.active_quantity == 8
	assert sku_a.reserved_quantity == 2
	assert sku_b.active_quantity == 4
	assert sku_b.reserved_quantity == 1


async def test_partial_insufficient_stock_returns_409_all_rollback(
	client: AsyncClient,
	reserve_inventory_data: ReserveInventoryData,
	db_session: AsyncSession,
) -> None:
	order_id = uuid.uuid4()
	response = await client.post(
		"/api/v1/inventory/reserve",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"idempotency_key": str(uuid.uuid4()),
			"order_id": str(order_id),
			"items": [
				{"sku_id": str(reserve_inventory_data.sku_a.id), "quantity": 5},
				{"sku_id": str(reserve_inventory_data.sku_low_stock.id), "quantity": 5},
			],
		},
	)
	assert response.status_code == 409
	body = response.json()
	assert body["code"] == "INSUFFICIENT_STOCK"
	failed = body["details"]["failed_items"]
	assert any(item["reason"] == "INSUFFICIENT_STOCK" for item in failed)

	sku_a = await _get_sku(db_session, reserve_inventory_data.sku_a.id)
	sku_low = await _get_sku(db_session, reserve_inventory_data.sku_low_stock.id)
	assert sku_a.active_quantity == 10
	assert sku_a.reserved_quantity == 0
	assert sku_low.active_quantity == 3
	assert sku_low.reserved_quantity == 0


async def test_idempotent_reserve_returns_200_without_double_deduction(
	client: AsyncClient,
	reserve_inventory_data: ReserveInventoryData,
	db_session: AsyncSession,
) -> None:
	order_id = uuid.uuid4()
	idempotency_key = uuid.uuid4()
	payload = {
		"idempotency_key": str(idempotency_key),
		"order_id": str(order_id),
		"items": [{"sku_id": str(reserve_inventory_data.sku_a.id), "quantity": 2}],
	}
	first = await client.post(
		"/api/v1/inventory/reserve",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json=payload,
	)
	second = await client.post(
		"/api/v1/inventory/reserve",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json=payload,
	)
	assert first.status_code == 200
	assert second.status_code == 200
	assert second.json()["reserved_at"] == first.json()["reserved_at"]

	sku_a = await _get_sku(db_session, reserve_inventory_data.sku_a.id)
	assert sku_a.active_quantity == 8
	assert sku_a.reserved_quantity == 2


async def test_sku_out_of_stock_event_emitted(
	client: AsyncClient,
	reserve_inventory_data: ReserveInventoryData,
	db_session: AsyncSession,
) -> None:
	response = await client.post(
		"/api/v1/inventory/reserve",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"idempotency_key": str(uuid.uuid4()),
			"order_id": str(uuid.uuid4()),
			"items": [
				{
					"sku_id": str(reserve_inventory_data.sku_oos_candidate.id),
					"quantity": 2,
				}
			],
		},
	)
	assert response.status_code == 200

	events = await _outbox_sku_out_of_stock_events(
		db_session, reserve_inventory_data.sku_oos_candidate.id
	)
	assert len(events) == 1
	assert events[0].payload["event_type"] == "SKU_OUT_OF_STOCK"
	assert events[0].payload["payload"]["available_quantity"] == 0

	sku = await _get_sku(db_session, reserve_inventory_data.sku_oos_candidate.id)
	assert sku.active_quantity == 0
	assert sku.reserved_quantity == 2


async def test_unreserve_restores_quantities(
	client: AsyncClient,
	reserve_inventory_data: ReserveInventoryData,
	db_session: AsyncSession,
) -> None:
	order_id = uuid.uuid4()
	await client.post(
		"/api/v1/inventory/reserve",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"idempotency_key": str(uuid.uuid4()),
			"order_id": str(order_id),
			"items": [
				{"sku_id": str(reserve_inventory_data.sku_a.id), "quantity": 3},
				{"sku_id": str(reserve_inventory_data.sku_b.id), "quantity": 1},
			],
		},
	)

	response = await client.post(
		"/api/v1/inventory/unreserve",
		headers=INVENTORY_SERVICE_KEY_HEADERS,
		json={
			"order_id": str(order_id),
			"items": [
				{"sku_id": str(reserve_inventory_data.sku_a.id), "quantity": 3},
				{"sku_id": str(reserve_inventory_data.sku_b.id), "quantity": 1},
			],
		},
	)
	assert response.status_code == 200
	assert response.json()["status"] == "UNRESERVED"

	sku_a = await _get_sku(db_session, reserve_inventory_data.sku_a.id)
	sku_b = await _get_sku(db_session, reserve_inventory_data.sku_b.id)
	assert sku_a.active_quantity == 10
	assert sku_a.reserved_quantity == 0
	assert sku_b.active_quantity == 5
	assert sku_b.reserved_quantity == 0
