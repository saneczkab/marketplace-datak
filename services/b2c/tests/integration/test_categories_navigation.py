import uuid

import pytest
from httpx import AsyncClient

from tests.integration.conftest import (
	CategoriesTreeData,
	CategoryWithProductsData,
	OrphanCategoryData,
)


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_category_tree_returns_nested_structure(
	client: AsyncClient,
	categories_tree: CategoriesTreeData,
) -> None:
	"""
	Test that category tree returns nested structure.
	"""
	response = await client.get("/api/v1/categories")
	body = response.json()

	assert response.status_code == 200
	assert body["items"][0]["id"] == str(categories_tree.root.id)
	assert body["items"][0]["children"][0]["id"] == str(categories_tree.child.id)
	assert body["items"][0]["children"][0]["children"][0]["id"] == str(
		categories_tree.grandchild.id
	)


async def test_breadcrumbs_return_path_from_root(
	client: AsyncClient,
	categories_tree: CategoriesTreeData,
) -> None:
	"""
	Test that breadcrumbs return path from root to grandchild category.
	"""
	response = await client.get(
		"/api/v1/breadcrumbs",
		params={"category_id": str(categories_tree.grandchild.id)},
	)
	body = response.json()

	assert response.status_code == 200
	assert body["data"][0]["id"] == str(categories_tree.root.id)
	assert body["data"][-1]["id"] == str(categories_tree.grandchild.id)
	assert body["data"][-1]["is_current"]


async def test_unknown_category_returns_404(client: AsyncClient) -> None:
	"""
	Test that unknown category returns 404.
	"""
	response = await client.get(f"/api/v1/categories/{uuid.uuid4()}")
	assert response.status_code == 404


async def test_orphan_node_returns_422(
	client: AsyncClient,
	orphan_category: OrphanCategoryData,
) -> None:
	"""
	Test that orphan category returns 422.
	"""
	response = await client.get(
		"/api/v1/breadcrumbs", params={"category_id": str(orphan_category.orphan.id)}
	)

	assert response.status_code == 422


async def test_ambiguous_params_returns_400(
	client: AsyncClient,
	categories_tree: CategoryWithProductsData,
) -> None:
	"""
	Test that ambiguous params returns 400.
	"""
	response = await client.get(
		"/api/v1/breadcrumbs",
		params={
			"category_id": str(categories_tree.root.id),
			"product_id": str(uuid.uuid4()),
		},
	)

	assert response.status_code == 400
