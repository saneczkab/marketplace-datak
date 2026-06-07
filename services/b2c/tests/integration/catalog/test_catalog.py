import pytest
from httpx import AsyncClient

from tests.integration.catalog.conftest import (
	CategoriesTreeData,
	CategoryWithProductsData,
	VisibilityProductsData,
)


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_facets_returns_empty_list_for_empty_category(
	client: AsyncClient,
	categories_tree: CategoriesTreeData,
) -> None:
	response = await client.get(
		"/api/v1/catalog/facets",
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
		"/api/v1/catalog/facets",
		params={"category_id": str(category_with_products.category.id)},
	)
	body = response.json()

	assert response.status_code == 200
	assert body["category_id"] == str(category_with_products.category.id)

	expected_filter_ids = {str(filter.id) for filter in category_with_products.filters}
	actual_filter_ids = {filter["id"] for filter in body["filters"]}
	assert expected_filter_ids == actual_filter_ids

	values = [val for facet in body["facets"] for val in facet.get("values", [])]
	values_by_value = {val["value"]: val["count"] for val in values}

	expected_values = {val.value for val in category_with_products.values}
	assert expected_values.issubset(values_by_value.keys())

	for value in expected_values:
		assert values_by_value[value] >= 1


async def test_catalog_returns_filtered_sorted_products(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
) -> None:
	category_id = str(category_with_products.category.id)
	base_url = f"/api/v1/catalog/products?filter[category_id]={category_id}"

	response = await client.get(base_url, params={"sort": "price_asc"})
	assert response.status_code == 200
	body = response.json()
	items = body["items"]
	assert len(items) == 2
	assert body["total_count"] == 2
	assert items[0]["id"] == str(category_with_products.products[0].id)
	assert items[1]["id"] == str(category_with_products.products[1].id)

	response_desc = await client.get(base_url, params={"sort": "price_desc"})
	assert response_desc.status_code == 200
	items_desc = response_desc.json()["items"]
	assert items_desc[0]["id"] == str(category_with_products.products[1].id)
	assert items_desc[1]["id"] == str(category_with_products.products[0].id)

	response_page = await client.get(
		base_url, params={"sort": "price_asc", "limit": 1, "offset": 0}
	)
	assert response_page.status_code == 200
	page_body = response_page.json()
	assert len(page_body["items"]) == 1
	assert page_body["total_count"] == 2
	assert page_body["limit"] == 1
	assert page_body["offset"] == 0
	assert page_body["items"][0]["id"] == str(category_with_products.products[0].id)


@pytest.mark.parametrize("sort", ["invalid", "title_asc", "title_desc"])
async def test_invalid_sort_returns_400(
	client: AsyncClient, category_with_products: CategoryWithProductsData, sort: str
) -> None:
	response = await client.get(
		"/api/v1/catalog/products?filter[category_id]="
		+ str(category_with_products.category.id),
		params={"sort": sort},
	)
	assert response.status_code == 400
	body = response.json()
	assert body["code"] == "INVALID_REQUEST"
	assert "Allowed:" in body["message"]


async def test_search_returns_matching_products(
	client: AsyncClient, category_with_products: CategoryWithProductsData
) -> None:
	category_id = str(category_with_products.category.id)
	base_url = f"/api/v1/catalog/products?filter[category_id]={category_id}"

	response_title = await client.get(base_url, params={"q": "Product 1"})
	assert response_title.status_code == 200
	items_title = response_title.json()["items"]
	assert len(items_title) == 1
	assert items_title[0]["id"] == str(category_with_products.products[0].id)

	response_description = await client.get(base_url, params={"q": "Description 1"})
	assert response_description.status_code == 200
	items_description = response_description.json()["items"]
	assert len(items_description) == 2
	ids = {item["id"] for item in items_description}
	assert ids == {
		str(category_with_products.products[0].id),
		str(category_with_products.products[1].id),
	}

	response_min_length = await client.get(base_url, params={"q": "Pro"})
	assert response_min_length.status_code == 200
	assert len(response_min_length.json()["items"]) >= 1


@pytest.mark.parametrize("search", ["t", "te"])
async def test_short_query_returns_400(
	client: AsyncClient, category_with_products: CategoryWithProductsData, search: str
) -> None:
	response = await client.get(
		"/api/v1/catalog/products?filter[category_id]="
		+ str(category_with_products.category.id),
		params={"q": search},
	)
	assert response.status_code == 400
	body = response.json()
	assert body["code"] == "INVALID_REQUEST"
	assert "at least 3 characters" in body["message"]


async def test_empty_results_returns_200(
	client: AsyncClient, category_with_products: CategoryWithProductsData
) -> None:
	response = await client.get(
		"/api/v1/catalog/products?filter[category_id]="
		+ str(category_with_products.category.id),
		params={"q": "Not exists"},
	)
	assert response.status_code == 200
	body = response.json()
	assert body["items"] == []


@pytest.mark.parametrize("search", ["iPhone%15", "кофе'", "!@#$%^&*()"])
async def test_special_chars_do_not_break_query(
	client: AsyncClient,
	category_with_products: CategoryWithProductsData,
	search: str,
) -> None:
	response = await client.get(
		"/api/v1/catalog/products?filter[category_id]="
		+ str(category_with_products.category.id),
		params={"q": search},
	)
	assert response.status_code == 200
	assert response.json()["items"] == []


async def test_products_list_filters_only_visible_products(
	client: AsyncClient,
	visibility_products: VisibilityProductsData,
) -> None:
	response = await client.get(
		"/api/v1/catalog/products?filter[category_id]="
		+ str(visibility_products.category.id),
	)
	assert response.status_code == 200
	body = response.json()
	ids = {item["id"] for item in body["items"]}
	assert str(visibility_products.visible_product.id) in ids
	assert str(visibility_products.hidden_by_status_product.id) not in ids
	assert str(visibility_products.hidden_by_stock_product.id) not in ids
