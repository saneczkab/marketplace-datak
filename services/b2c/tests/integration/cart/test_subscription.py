import uuid
from httpx import AsyncClient
from tests.integration.cart.conftest import SubscriptionsData
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_subscribe_returns_201_with_notify_on(
	client: AsyncClient,
	empty_subscriptions_data: SubscriptionsData,
) -> None:
	product = empty_subscriptions_data.product
	response = await client.post(
		f"/api/v1/favorites/{product.id}/subscribe",
		params={
			"product_id": product.id,
		},
		json={"notify_on": ["IN_STOCK"]},
	)
	assert response.status_code == 201
	body = response.json()
	assert body["product"]["id"] == str(product.id)


async def test_duplicate_subscription_returns_409(
	client: AsyncClient,
	subscriptions_data: SubscriptionsData,
) -> None:
	product = subscriptions_data.product
	response = await client.post(
		f"/api/v1/favorites/{product.id}/subscribe",
		params={
			"product_id": product.id,
		},
		json={"notify_on": ["IN_STOCK"]},
	)
	assert response.status_code == 409


async def test_invalid_notify_on_returns_400(
	client: AsyncClient,
	empty_subscriptions_data: SubscriptionsData,
) -> None:
	product = empty_subscriptions_data.product
	response = await client.post(
		f"/api/v1/favorites/{product.id}/subscribe",
		params={
			"product_id": product.id,
		},
	)
	assert response.status_code == 400


async def test_subscribe_to_unknown_product_returns_404(
	client: AsyncClient,
) -> None:
	response = await client.post(
		f"/api/v1/favorites/{uuid.uuid4()}/subscribe",
		params={
			"product_id": uuid.uuid4(),
		},
		json={"notify_on": ["IN_STOCK"]},
	)
	assert response.status_code == 404
