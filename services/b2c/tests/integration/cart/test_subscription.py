import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.user import UserFactory
from tests.integration.cart.conftest import SubscriptionsData, auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_subscribe_returns_204(
	client: AsyncClient,
	db_session: AsyncSession,
	empty_subscriptions_data: SubscriptionsData,
) -> None:
	product = empty_subscriptions_data.product
	response = await client.post(
		f"/api/v1/favorites/{product.id}/subscribe",
		json={"events": ["BACK_IN_STOCK"]},
		headers=await auth_headers(empty_subscriptions_data.user.id, db_session),
	)
	assert response.status_code == 204
	assert response.content == b""


async def test_duplicate_subscription_returns_204(
	client: AsyncClient,
	db_session: AsyncSession,
	subscriptions_data: SubscriptionsData,
) -> None:
	product = subscriptions_data.product
	response = await client.post(
		f"/api/v1/favorites/{product.id}/subscribe",
		json={"events": ["BACK_IN_STOCK"]},
		headers=await auth_headers(subscriptions_data.user.id, db_session),
	)
	assert response.status_code == 204


async def test_invalid_events_returns_422(
	client: AsyncClient,
	db_session: AsyncSession,
	empty_subscriptions_data: SubscriptionsData,
) -> None:
	product = empty_subscriptions_data.product
	response = await client.post(
		f"/api/v1/favorites/{product.id}/subscribe",
		headers=await auth_headers(empty_subscriptions_data.user.id, db_session),
		json={"events": ["INVALID"]},
	)
	assert response.status_code == 422


async def test_subscribe_to_unknown_product_returns_404(
	client: AsyncClient,
	db_session: AsyncSession,
) -> None:
	user = UserFactory.build()
	db_session.add(user)
	await db_session.commit()

	response = await client.post(
		f"/api/v1/favorites/{uuid.uuid4()}/subscribe",
		json={"events": ["BACK_IN_STOCK"]},
		headers=await auth_headers(user.id, db_session),
	)
	assert response.status_code == 404
