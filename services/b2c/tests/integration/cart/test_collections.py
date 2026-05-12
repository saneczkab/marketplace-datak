import uuid
from httpx import AsyncClient
import pytest

from database.models.catalog.base import ProductStatusEnum
from tests.integration.cart.conftest import CollectionsData

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_collections_list_returns_metadata_without_products(
	client: AsyncClient,
	collections_data: CollectionsData,
) -> None:
	response = await client.get("/api/v1/main/collections")
	assert response.status_code == 200
	body = response.json()
	assert len(body["collections"]) == len(collections_data.collections)
	assert all(
		collection["id"]
		in [str(collection.id) for collection in collections_data.collections]
		for collection in body["collections"]
	)
	assert body["metadata"]["total_count"] == len(collections_data.collections)
	assert body["metadata"]["limit"] == 10
	assert body["metadata"]["offset"] == 0
	for collection in body["collections"]:
		assert "products" not in collection
		assert "product" not in collection


async def test_unknown_collection_returns_404(
	client: AsyncClient,
) -> None:
	response = await client.get(f"/api/v1/main/collections/{uuid.uuid4()}")
	assert response.status_code == 404


async def test_unavailable_products_in_unavailable_ids(
	client: AsyncClient,
	collections_data: CollectionsData,
) -> None:
	response = await client.get(
		f"/api/v1/collections/{collections_data.collections[0].id}/products"
	)
	assert response.status_code == 200
	body = response.json()
	assert body["unavailable_ids"] == [
		str(product.id)
		for product in collections_data.products
		if product.status != ProductStatusEnum.MODERATED
	]


async def test_collection_products_enriched_from_b2b(
	client: AsyncClient,
	collections_data: CollectionsData,
) -> None:
	collection_id = collections_data.collections[0].id
	response = await client.get(f"/api/v1/collections/{collection_id}/products")
	assert response.status_code == 200
	body = response.json()

	product_ids_in_collection = {
		cp.product_id
		for cp in collections_data.collection_products
		if cp.collection_id == collection_id
	}
	assert len(body["items"]) == len(product_ids_in_collection)
	assert body["total_products"] == len(product_ids_in_collection)

	products_by_id = {p.id: p for p in collections_data.products}
	skus_by_product_id = {s.product_id: s for s in collections_data.skus}

	returned_ids = {uuid.UUID(item["id"]) for item in body["items"]}
	assert returned_ids == product_ids_in_collection

	for item in body["items"]:
		pid = uuid.UUID(item["id"])
		product = products_by_id[pid]
		sku = skus_by_product_id[pid]
		assert item["title"] == product.title
		assert item["description"] == (product.description or "")
		assert item["status"] == product.status.name
		assert item["category"]["id"] == str(product.category_id)
		assert item["category"]["name"] == collections_data.categories[0].name
		assert item["images"] == []
		assert item["characteristics"] == []
		assert len(item["skus"]) == 1
		assert item["skus"][0]["id"] == str(sku.id)
		assert item["skus"][0]["name"] == sku.name
		assert item["skus"][0]["price"] == sku.price
		assert item["skus"][0]["active_quantity"] == sku.active_quantity
		assert item["skus"][0]["characteristics"] == []
