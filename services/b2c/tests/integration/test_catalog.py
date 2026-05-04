import uuid

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_facets_returns_empty_list_for_empty_category(
	client: AsyncClient,
	categories_tree: dict[str, uuid.UUID],
) -> None:
	response = await client.get(
		"/api/v1/catalog/facets/",
		params={"category_id": str(categories_tree["grandchild"])},
	)
	body = response.json()

	assert response.status_code == 200
	assert body["category_id"] == str(categories_tree["grandchild"])
	assert body["facets"] == []


async def test_facets_return_counts_per_filter_value(
	client: AsyncClient,
	category_with_products: dict[str, uuid.UUID],
) -> None:
	response = await client.get(
		"/api/v1/catalog/facets/",
		params={"category_id": str(category_with_products["category_with_filters"])},
	)
	body = response.json()

	assert response.status_code == 200
	assert body["category_id"] == str(category_with_products["category_with_filters"])
	filter_ids = [filter["id"] for filter in body["filters"]]
	assert len(filter_ids) == 2
	assert category_with_products["filter_1"] in filter_ids
	assert category_with_products["filter_2"] in filter_ids
	facet_values = [facet["values"] for facet in body["facets"]]
	assert len(facet_values) == 2
	assert facet_values[0]["value"] == "Value 1"
	assert facet_values[0]["count"] == 1
	assert facet_values[1]["value"] == "Value 2"
	assert facet_values[1]["count"] == 1
