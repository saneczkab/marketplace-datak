import pytest
from httpx import AsyncClient

from tests.integration.conftest import CategoriesTreeData, CategoryWithProductsData


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_facets_returns_empty_list_for_empty_category(
	client: AsyncClient,
	categories_tree: CategoriesTreeData,
) -> None:
	response = await client.get(
		"/api/v1/catalog/facets/",
		params={"category_id": str(categories_tree.grandchild.id)},
	)
	body = response.json()

	assert response.status_code == 200
	assert body["category_id"] == str(categories_tree.grandchild.id)
	assert body["facets"] == []


async def test_facets_return_counts_per_filter_value(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
) -> None:
	response = await client.get(
		"/api/v1/catalog/facets/",
		params={"category_id": str(category_with_products.category.id)},
	)
	body = response.json()

	assert response.status_code == 200
	assert body["category_id"] == str(category_with_products.category.id)
	filter_ids = [filter["id"] for filter in body["filters"]]
	assert len(filter_ids) == 2
	assert str(category_with_products.filters[0].id) in filter_ids
	assert str(category_with_products.filters[1].id) in filter_ids
	facet_values = [facet["values"] for facet in body["facets"]]
	assert len(facet_values) == 2
	assert facet_values[0]["value"] == "Value 1"
	assert facet_values[0]["count"] == 1
	assert facet_values[1]["value"] == "Value 2"
	assert facet_values[1]["count"] == 1


async def test_catalog_returns_filtered_sorted_products(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
) -> None:
	response = await client.get(
		"/api/v1/products",
		params={
			"category_id": str(category_with_products.category.id),
		},
	)

	assert response.status_code == 200
	body = response.json()
	items = body["items"]
	assert len(items) == 2
	assert body["total_count"] == 2
	assert items[0]["id"] == str(category_with_products.products[0].id)
	assert items[1]["id"] == str(category_with_products.products[1].id)


@pytest.mark.parametrize("sort", ["invalid", "title_asc", "title_desc"])
async def test_invalid_sort_returns_400(
	client: AsyncClient, category_with_products: CategoryWithProductsData, sort: str
) -> None:
	response = await client.get(
		"/api/v1/products",
		params={"category_id": str(category_with_products.category.id), "sort": sort},
	)
	assert response.status_code == 400
