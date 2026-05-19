import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import ProductStatusEnum
from tests.factories.user import UserFactory
from tests.integration.cart.conftest import FavoritesData, auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_add_to_favorites_returns_201(
	client: AsyncClient,
	db_session: AsyncSession,
	empty_favorites_data: FavoritesData,
) -> None:
	product = empty_favorites_data.products[0]
	response = await client.post(
		f"/api/v1/favorites/{product.id}",
		headers=await auth_headers(empty_favorites_data.user.id, db_session),
	)
	assert response.status_code == 201
	body = response.json()
	assert body["product_id"] == str(product.id)
	assert body["user_id"] == str(empty_favorites_data.user.id)


async def test_repeat_add_returns_200_not_duplicate(
	client: AsyncClient,
	db_session: AsyncSession,
	favorites_data: FavoritesData,
) -> None:
	product = favorites_data.products[0]
	response = await client.post(
		f"/api/v1/favorites/{product.id}",
		headers=await auth_headers(favorites_data.user.id, db_session),
	)
	assert response.status_code == 200
	body = response.json()
	assert body["product_id"] == str(product.id)
	assert body["user_id"] == str(favorites_data.user.id)


async def test_locked_product_excluded_from_list(
	client: AsyncClient,
	db_session: AsyncSession,
	favorites_data: FavoritesData,
) -> None:
	moderated_product = next(
		product for product in favorites_data.products if product.status == ProductStatusEnum.MODERATED
	)
	blocked_product = next(
		product for product in favorites_data.products if product.status == ProductStatusEnum.BLOCKED
	)
	response = await client.get(
		"/api/v1/favorites",
		headers=await auth_headers(favorites_data.user.id, db_session),
	)
	assert response.status_code == 200
	body = response.json()

	returned_product_ids = {item["product"]["id"] for item in body["items"]}
	assert str(moderated_product.id) in returned_product_ids
	assert str(blocked_product.id) not in returned_product_ids
	assert len(body["items"]) == 1
	assert body["total"] == 1


async def test_user_id_from_query_is_ignored(
	client: AsyncClient,
	db_session: AsyncSession,
	favorites_data: FavoritesData,
) -> None:
	other_user = UserFactory.build()
	db_session.add(other_user)
	await db_session.commit()

	victim_response = await client.get(
		"/api/v1/favorites",
		headers=await auth_headers(favorites_data.user.id, db_session),
	)
	assert len(victim_response.json()["items"]) == 1

	response = await client.get(
		"/api/v1/favorites",
		params={"user_id": str(favorites_data.user.id)},
		headers=await auth_headers(other_user.id, db_session),
	)
	assert response.status_code == 200
	assert response.json()["items"] == []


async def test_delete_from_favorites_returns_204(
	client: AsyncClient,
	db_session: AsyncSession,
	favorites_data: FavoritesData,
) -> None:
	product = favorites_data.products[0]
	response = await client.delete(
		f"/api/v1/favorites/{product.id}",
		headers=await auth_headers(favorites_data.user.id, db_session),
	)
	assert response.status_code == 204


async def test_delete_non_existent_product_returns_404(
	client: AsyncClient,
	db_session: AsyncSession,
	favorites_data: FavoritesData,
) -> None:
	response = await client.delete(
		f"/api/v1/favorites/{uuid.uuid4()}",
		headers=await auth_headers(favorites_data.user.id, db_session),
	)
	assert response.status_code == 404


async def test_favorites_requires_authorization(
	client: AsyncClient,
	favorites_data: FavoritesData,
) -> None:
	product = favorites_data.products[0]
	response = await client.get("/api/v1/favorites")
	assert response.status_code == 401

	response = await client.post(f"/api/v1/favorites/{product.id}")
	assert response.status_code == 401

	response = await client.delete(f"/api/v1/favorites/{product.id}")
	assert response.status_code == 401
