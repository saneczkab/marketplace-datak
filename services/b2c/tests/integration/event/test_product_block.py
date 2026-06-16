import pytest
import logging
from httpx import AsyncClient, Response
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.inbox import process_events

from tests.integration.cart.conftest import auth_headers
from tests.integration.event.conftest import BlockingProductInCart, product_with_block

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_block_product(
	client: AsyncClient,
	product_with_block: product_with_block,
) -> None:
	service_key = settings.X_SERVICE_KEY

	response = await client.post(
		"/api/v1/b2b/events",
		headers={"X-Service-key": service_key},
		json={
			"event_type": "PRODUCT_BLOCKED",
			"idempotency_key": f"{product_with_block.idempotency_key}",
			"occured_at": f"{datetime.now(timezone.utc)}",
			"payload": {
				"type": "product_ref",
				"product_id": str(product_with_block.product.id),
				"reason": product_with_block.reason.reason,
			},
		},
	)

	assert response.status_code == 202


async def test_block_product_idempotency(
	client: AsyncClient,
	product_with_block: product_with_block,
) -> None:
	service_key = settings.X_SERVICE_KEY

	await client.post(
		"/api/v1/b2b/events",
		headers={"X-Service-key": service_key},
		json={
			"event_type": "PRODUCT_BLOCKED",
			"idempotency_key": f"{product_with_block.idempotency_key}",
			"occured_at": f"{datetime.now(timezone.utc)}",
			"payload": {
				"type": "product_ref",
				"product_id": str(product_with_block.product.id),
				"reason": product_with_block.reason.reason,
			},
		},
	)

	response = await client.post(
		"/api/v1/b2b/events",
		headers={"X-Service-key": service_key},
		json={
			"event_type": "PRODUCT_BLOCKED",
			"idempotency_key": f"{product_with_block.idempotency_key}",
			"occured_at": f"{datetime.now(timezone.utc)}",
			"payload": {
				"type": "product_ref",
				"product_id": str(product_with_block.product.id),
				"reason": product_with_block.reason.reason,
			},
		},
	)

	assert response.status_code == 409


async def test_missing_service_key_returns_401(
	client: AsyncClient,
	product_with_block: product_with_block,
) -> None:
	response = await client.post(
		"/api/v1/b2b/events",
		json={
			"event_type": "PRODUCT_BLOCKED",
			"idempotency_key": f"{product_with_block.idempotency_key}",
			"occured_at": f"{datetime.now(timezone.utc)}",
			"payload": {
				"type": "product_ref",
				"product_id": str(product_with_block.product.id),
				"reason": product_with_block.reason.reason,
			},
		},
	)

	assert response.status_code == 401


async def test_hard_block_product(
	client: AsyncClient,
	product_with_block: product_with_block,
) -> None:
	service_key = settings.X_SERVICE_KEY

	response = await client.post(
		"/api/v1/b2b/events",
		headers={"X-Service-key": service_key},
		json={
			"event_type": "PRODUCT_HARD_BLOCKED",
			"idempotency_key": f"{product_with_block.idempotency_key}",
			"occured_at": f"{datetime.now(timezone.utc)}",
			"payload": {
				"type": "product_ref",
				"product_id": str(product_with_block.product.id),
				"reason": product_with_block.reason.reason,
			},
		},
	)

	assert response.status_code == 202


async def test_product_block_deletes_from_cart(
	client: AsyncClient,
	db_session: AsyncSession,
	caplog: pytest.LogCaptureFixture,
	product_in_cart_with_block: BlockingProductInCart,
) -> None:
	service_key = settings.X_SERVICE_KEY

	caplog.set_level(logging.INFO)

	response = await client.post(
		"/api/v1/b2b/events",
		headers={"X-Service-key": service_key},
		json={
			"event_type": "PRODUCT_BLOCKED",
			"idempotency_key": f"{product_in_cart_with_block.idempotency_key}",
			"occured_at": f"{datetime.now(timezone.utc)}",
			"payload": {
				"type": "product_ref",
				"product_id": str(product_in_cart_with_block.product.id),
				"reason": product_in_cart_with_block.reason.reason,
			},
		},
	)

	assert response.status_code == 202

	# await asyncio.sleep(
	# 	settings.INBOX_MESSAGES_PROCESSING_DELAY + 1
	# )  # needs time to process message

	await process_events()  # Temporary solution

	response: Response = await client.get(
		"/api/v1/cart",
		headers=await auth_headers(product_in_cart_with_block.user.id, db_session),
	)

	body = response.json()
	assert len(body["items"]) == 0
