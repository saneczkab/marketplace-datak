from uuid import uuid4

import pytest
from httpx import AsyncClient

from database.models import Seller

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_get_seller_info(client: AsyncClient, seller_data: Seller) -> None:
	response = await client.get(f"/api/v1/sellers/{seller_data.id}")

	assert response.status_code == 200
	body = response.json()

	assert body["id"] == str(seller_data.id)


async def test_get_seller_info_no_seller_returns_404(client: AsyncClient) -> None:
	response = await client.get(f"/api/v1/sellers/{uuid4()}")

	assert response.status_code == 404
	body = response.json()
	assert body["code"] == "NOT_FOUND_ERROR"
