import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import SellerUpdateData, auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_update_seller_updates_data(
	client: AsyncClient, seller_update_data: SellerUpdateData, db_session: AsyncSession
) -> None:
	data = seller_update_data
	headers = await auth_headers(data.seller.id, db_session)

	response = await client.patch(
		f"/api/v1/sellers/{data.seller.id}",
		headers=headers,
		json=data.patch_data.model_dump(mode="json"),
	)

	assert response.status_code == 200
	body = response.json()

	assert body["first_name"] == data.patch_data.first_name
	assert body["last_name"] == data.patch_data.last_name
	assert body["middle_name"] == data.patch_data.middle_name
	assert body["company_name"] == data.patch_data.company_name
	# Can't check phone and email - none of the handlers return private data
