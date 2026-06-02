from httpx import AsyncClient
import pytest

from core.config import settings

from tests.integration.event.confest import product_with_block

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
			"idempotency_key": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
			"occured_at": "2026-06-02T06:33:51.835Z",
			"payload": {
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
			"idempotency_key": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
			"occured_at": "2026-06-02T06:33:51.835Z",
			"payload": {
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
			"idempotency_key": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
			"occured_at": "2026-06-02T06:33:51.835Z",
			"payload": {
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
			"idempotency_key": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
			"occured_at": "2026-06-02T06:33:51.835Z",
			"payload": {
				"product_id": str(product_with_block.product.id),
				"reason": product_with_block.reason.reason,
			},
		},
	)

	assert response.status_code == 401
