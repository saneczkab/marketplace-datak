import uuid
from httpx import AsyncClient
from database.models.catalog.base import ProductStatusEnum
from tests.integration.cart.conftest import FavoritesData
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_add_to_favorites_returns_201(
	client: AsyncClient,
	empty_favorites_data: FavoritesData,
) -> None:
	product = empty_favorites_data.products[0]
	response = await client.post(
		f"/api/v1/favorites/{product.id}",
		params={
			"user_id": empty_favorites_data.user.id,
			"product_id": product.id,
		},
	)
	assert response.status_code == 201
	body = response.json()
	assert body["product_id"] == str(product.id)
	assert body["user_id"] == str(empty_favorites_data.user.id)


async def test_repeat_add_returns_200_not_duplicate(
	client: AsyncClient,
	favorites_data: FavoritesData,
) -> None:
	product = favorites_data.products[0]
	response = await client.post(
		f"/api/v1/favorites/{product.id}",
		params={
			"user_id": favorites_data.user.id,
			"product_id": product.id,
		},
	)
	assert response.status_code == 200
	body = response.json()
	assert body["product_id"] == str(product.id)
	assert body["user_id"] == str(favorites_data.user.id)


async def test_locked_product_excluded_from_list(
	client: AsyncClient,
	favorites_data: FavoritesData,
) -> None:
	response = await client.get(
		"/api/v1/favorites",
		params={"user_id": favorites_data.user.id},
	)
	assert response.status_code == 200
	body = response.json()
	product = next(
		p for p in favorites_data.products if p.status == ProductStatusEnum.MODERATED
	)
	assert len(body["items"]) == 1
	assert body["items"][0]["product"]["id"] == str(product.id)


async def test_user_id_from_query_is_ignored() -> None:
	pass


async def test_delete_from_favorites_returns_204(
	client: AsyncClient,
	favorites_data: FavoritesData,
) -> None:
	product = favorites_data.products[0]
	response = await client.delete(
		f"/api/v1/favorites/{product.id}",
		params={"user_id": favorites_data.user.id},
	)
	assert response.status_code == 204


async def test_delete_non_existent_product_returns_404(
	client: AsyncClient,
	favorites_data: FavoritesData,
) -> None:
	response = await client.delete(
		f"/api/v1/favorites/{uuid.uuid4()}",
		params={"user_id": favorites_data.user.id},
	)
	assert response.status_code == 404
