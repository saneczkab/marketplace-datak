import uuid
import pytest
from httpx import AsyncClient

from tests.integration.conftest import SimilarProductsData


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_similar_returns_up_to_8_from_same_category(
	client: AsyncClient,
	similar_products_data: SimilarProductsData,
) -> None:
	base = similar_products_data.base_product
	category = similar_products_data.category
	candidate_ids = {
		str(product.id) for product in similar_products_data.similar_products
	}
	other_ids = {str(product.id) for product in similar_products_data.other_products}

	response = await client.get(
		f"/api/v1/products/{base.id}/similar",
		params={"category": str(category.id)},
	)

	assert response.status_code == 200
	body = response.json()

	items = body["items"]
	ids = [item["id"] for item in items]

	assert len(items) == 8
	assert body["total_count"] == len(similar_products_data.similar_products)

	assert str(base.id) not in ids
	assert set(ids).issubset(candidate_ids)
	assert set(ids).isdisjoint(other_ids)


async def test_empty_category_returns_200_empty_list(
	client: AsyncClient,
	one_product_category: SimilarProductsData,
) -> None:
	base = one_product_category.base_product
	response = await client.get(
		f"/api/v1/products/{base.id}/similar",
		params={"category": str(one_product_category.other_category.id)},
	)
	assert response.status_code == 200
	body = response.json()
	assert body["items"] == []
	assert body["total_count"] == 0


async def test_unknown_product_returns_404(
	client: AsyncClient,
	similar_products_data: SimilarProductsData,
) -> None:
	response = await client.get(
		f"/api/v1/products/{uuid.uuid4()}/similar",
		params={"category": str(similar_products_data.category.id)},
	)
	assert response.status_code == 404


async def test_unknown_category_returns_400(
	client: AsyncClient,
	similar_products_data: SimilarProductsData,
) -> None:
	response = await client.get(
		f"/api/v1/products/{similar_products_data.base_product.id}/similar",
		params={"category": uuid.uuid4()},
	)
	assert response.status_code == 400
