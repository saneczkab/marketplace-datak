import uuid
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import pytest
from tests.integration.order.conftest import (
	FakeB2BClient,
	OrderData,
	override_b2b_client,
)
from tests.integration.cart.conftest import auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_cancel_paid_order_transitions_to_cancelled(
	client: AsyncClient,
	db_session: AsyncSession,
	order_data: OrderData,
	default_b2b_client: FakeB2BClient,
) -> None:
	response = await client.post(
		f"/api/v1/orders/{order_data.order.id}/cancel",
		headers=await auth_headers(order_data.order.buyer_id, db_session),
	)
	assert response.status_code == 200
	body = response.json()
	assert body["id"] == str(order_data.order.id)
	assert body["status"] == "CANCELLED"
	assert body["status_history"][0]["status"] == "PAID"
	assert body["status_history"][1]["status"] == "CANCEL_PENDING"
	assert body["status_history"][2]["status"] == "CANCELLED"
	assert len(default_b2b_client.unreserve_calls) == 1
	unreserve_call = default_b2b_client.unreserve_calls[0]
	assert unreserve_call["order_id"] == order_data.order.id
	assert {item["sku_id"] for item in unreserve_call["items"]} == {
		str(order_item.sku_id) for order_item in order_data.order_items
	}


async def test_unreserve_failure_transitions_to_cancel_pending(
	client: AsyncClient,
	db_session: AsyncSession,
	order_data: OrderData,
	app: FastAPI,
) -> None:
	b2b_client = override_b2b_client(
		app, FakeB2BClient(unreserve_behavior="unavailable")
	)
	response = await client.post(
		f"/api/v1/orders/{order_data.order.id}/cancel",
		headers=await auth_headers(order_data.order.buyer_id, db_session),
	)
	assert response.status_code == 200
	body = response.json()
	assert body["status"] == "CANCEL_PENDING"
	assert body["status_history"][-1]["status"] == "CANCEL_PENDING"
	assert len(b2b_client.unreserve_calls) == 1


async def test_other_user_order_returns_404(
	client: AsyncClient,
	db_session: AsyncSession,
	order_data: OrderData,
) -> None:
	response = await client.post(
		f"/api/v1/orders/{order_data.order.id}/cancel",
		headers=await auth_headers(uuid.uuid4(), db_session),
	)
	assert response.status_code == 404
	body = response.json()
	assert body["code"] == "NOT_FOUND"
	assert body["message"] == "Order not found"


async def test_cancel_assembling_order_transitions_to_cancelled(
	client: AsyncClient,
	db_session: AsyncSession,
	assembling_order_data: OrderData,
	default_b2b_client: FakeB2BClient,
) -> None:
	response = await client.post(
		f"/api/v1/orders/{assembling_order_data.order.id}/cancel",
		headers=await auth_headers(assembling_order_data.order.buyer_id, db_session),
	)
	assert response.status_code == 200
	body = response.json()
	assert body["status"] == "CANCELLED"
	assert body["status_history"][0]["status"] == "ASSEMBLING"
	assert body["status_history"][1]["status"] == "CANCEL_PENDING"
	assert body["status_history"][2]["status"] == "CANCELLED"
	assert len(default_b2b_client.unreserve_calls) == 1


async def test_cancel_delivered_order_returns_409(
	client: AsyncClient,
	db_session: AsyncSession,
	delivered_order_data: OrderData,
	default_b2b_client: FakeB2BClient,
) -> None:
	response = await client.post(
		f"/api/v1/orders/{delivered_order_data.order.id}/cancel",
		headers=await auth_headers(delivered_order_data.order.buyer_id, db_session),
	)
	assert response.status_code == 409
	body = response.json()
	assert body["code"] == "CANCEL_NOT_ALLOWED"
	assert body["message"] == "Can't cancel order in this state"
	assert len(default_b2b_client.unreserve_calls) == 0


async def test_cancel_order_not_authorized_returns_401(
	client: AsyncClient,
	order_data: OrderData,
) -> None:
	response = await client.post(
		f"/api/v1/orders/{order_data.order.id}/cancel",
		headers={},
	)
	assert response.status_code == 401


async def test_cancel_delivering_order_transitions_to_cancelled(
	client: AsyncClient,
	db_session: AsyncSession,
	delivering_order_data: OrderData,
	default_b2b_client: FakeB2BClient,
) -> None:
	response = await client.post(
		f"/api/v1/orders/{delivering_order_data.order.id}/cancel",
		headers=await auth_headers(delivering_order_data.order.buyer_id, db_session),
	)
	assert response.status_code == 200
	body = response.json()
	assert body["status"] == "CANCELLED"
	assert body["status_history"][0]["status"] == "DELIVERING"
	assert body["status_history"][1]["status"] == "CANCEL_PENDING"
	assert body["status_history"][2]["status"] == "CANCELLED"
	assert len(default_b2b_client.unreserve_calls) == 1
