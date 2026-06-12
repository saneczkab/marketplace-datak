import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import SellerListData, auth_headers

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_list_returns_only_own_products(
	client: AsyncClient,
	seller_list_data: SellerListData,
	db_session: AsyncSession,
) -> None:
	data = seller_list_data
	headers = await auth_headers(data.owner.id, db_session)

	response = await client.get("/api/v1/products", headers=headers)
	assert response.status_code == 200
	body = response.json()

	ids = {item["id"] for item in body["items"]}
	assert str(data.moderated_product.id) in ids
	assert str(data.other_seller_product.id) not in ids
	assert body["total_count"] == 4
	assert body["limit"] == 20
	assert body["offset"] == 0


async def test_idor_query_param_seller_id_ignored(
	client: AsyncClient,
	seller_list_data: SellerListData,
	db_session: AsyncSession,
) -> None:
	data = seller_list_data
	headers = await auth_headers(data.owner.id, db_session)

	baseline = await client.get("/api/v1/products", headers=headers)
	spoofed = await client.get(
		f"/api/v1/products?seller_id={data.other_seller.id}",
		headers=headers,
	)
	assert spoofed.status_code == 200

	baseline_ids = {i["id"] for i in baseline.json()["items"]}
	spoofed_ids = {i["id"] for i in spoofed.json()["items"]}
	assert baseline_ids == spoofed_ids
	assert str(data.other_seller_product.id) not in spoofed_ids


async def test_deleted_products_visible_with_deleted_flag(
	client: AsyncClient,
	seller_list_data: SellerListData,
	db_session: AsyncSession,
) -> None:
	data = seller_list_data
	headers = await auth_headers(data.owner.id, db_session)

	response = await client.get("/api/v1/products", headers=headers)
	body = response.json()

	deleted_items = [
		i for i in body["items"] if i["id"] == str(data.deleted_product.id)
	]
	assert len(deleted_items) == 1
	assert deleted_items[0]["deleted"] is True


async def test_status_filter_works_correctly(
	client: AsyncClient,
	seller_list_data: SellerListData,
	db_session: AsyncSession,
) -> None:
	data = seller_list_data
	headers = await auth_headers(data.owner.id, db_session)

	response = await client.get("/api/v1/products?status=BLOCKED", headers=headers)
	body = response.json()

	assert body["total_count"] == 1
	ids = {i["id"] for i in body["items"]}
	assert ids == {str(data.blocked_product.id)}
	for item in body["items"]:
		assert item["status"] == "BLOCKED"


async def test_search_by_title_case_insensitive(
	client: AsyncClient,
	seller_list_data: SellerListData,
	db_session: AsyncSession,
) -> None:
	data = seller_list_data
	headers = await auth_headers(data.owner.id, db_session)

	response = await client.get("/api/v1/products?search=IPHONE", headers=headers)
	body = response.json()

	ids = {i["id"] for i in body["items"]}
	assert str(data.moderated_product.id) in ids
	assert str(data.blocked_product.id) not in ids


async def test_response_includes_sku_aggregates(
	client: AsyncClient,
	seller_list_data: SellerListData,
	db_session: AsyncSession,
) -> None:
	data = seller_list_data
	headers = await auth_headers(data.owner.id, db_session)

	response = await client.get("/api/v1/products", headers=headers)
	body = response.json()

	moderated = next(
		i for i in body["items"] if i["id"] == str(data.moderated_product.id)
	)
	assert moderated["skus_count"] == 2
	assert moderated["total_active_quantity"] == 15
	assert moderated["category"]["name"] == "Смартфоны"


async def test_pagination_limit_offset_works(
	client: AsyncClient,
	seller_list_data: SellerListData,
	db_session: AsyncSession,
) -> None:
	data = seller_list_data
	headers = await auth_headers(data.owner.id, db_session)

	page1 = await client.get("/api/v1/products?limit=2&offset=0", headers=headers)
	page2 = await client.get("/api/v1/products?limit=2&offset=2", headers=headers)
	b1, b2 = page1.json(), page2.json()

	assert b1["total_count"] == 4
	assert b1["limit"] == 2
	assert b1["offset"] == 0
	assert len(b1["items"]) == 2
	assert len(b2["items"]) == 2
	ids1 = {i["id"] for i in b1["items"]}
	ids2 = {i["id"] for i in b2["items"]}
	assert ids1.isdisjoint(ids2)
