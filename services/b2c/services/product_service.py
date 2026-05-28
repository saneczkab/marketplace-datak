import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

import crud.product as product_crud
import crud.category as category_crud
from database.models import Sku
from exceptions.category import CategoryNotFoundError
from exceptions.product import (
	ProductNotFoundError,
	InvalidSortError,
	InvalidSearchQueryError,
)
from schemas.product import (
	ProductShort,
	Product,
	ProductShortListResponse,
	SimilarProductsResponse,
)
from schemas.sku import SkuShort
from schemas.image import Image
from schemas.category import FacetsResponse


async def get_product_skus(db: AsyncSession, product_id: uuid.UUID) -> list[Sku]:
	"""
	Gets a SKU by its ID
	:param db: database session
	:param product_id: SKU ID
	:return: SKU or None if not found
	:raises ProductNotFoundError: if product not found
	"""
	skus = await product_crud.get_product_skus(db, product_id)

	if not skus:
		raise ProductNotFoundError

	return skus


async def get_product_skus_short(
	db: AsyncSession, product_id: uuid.UUID
) -> list[SkuShort]:
	"""
	Gets SKUs in short format by product ID
	:param db: database session
	:param product_id: Product ID
	:return: List of SKUs in short format
	:raises ProductNotFoundError: if product not found
	"""
	skus = await product_crud.get_product_skus(db, product_id)

	if not skus:
		raise ProductNotFoundError

	return [
		SkuShort(
			name=sku.name,
			price=sku.price,
			image=sku.images[0] if sku.images else Image(url="", order=0),
		)
		for sku in skus
	]


async def get_products_list(
	db: AsyncSession,
	limit: int,
	offset: int,
	category_id: Optional[str],
	filters_dict: Optional[dict],
	sort: str,
	q: Optional[str],
) -> ProductShortListResponse:
	valid_sorts = [
		"rating",
		"popularity",
		"price_asc",
		"price_desc",
		"date_desc",
		"discount_desc",
	]
	if sort not in valid_sorts:
		raise InvalidSortError(
			f"Invalid sort parameter. Allowed: {', '.join(valid_sorts)}"
		)

	if q:
		search_stripped = q.strip()
		if 0 < len(search_stripped) < 3:
			raise InvalidSearchQueryError("Search query must be at least 3 characters")
		if len(search_stripped) > 255:
			raise InvalidSearchQueryError("Search query must be at most 255 characters")

	parsed_category_id = uuid.UUID(category_id) if category_id else None

	products, total = await product_crud.get_products_list(
		db=db,
		limit=limit,
		offset=offset,
		category_id=parsed_category_id,
		filter=filters_dict,
		sort=sort,
		q=q,
	)

	return ProductShortListResponse(items=products, total_count=total)


async def get_catalog_facets_service(
	db: AsyncSession,  # noqa
	category_id: str,
	filters_dict: Optional[dict],  # noqa
) -> FacetsResponse:
	return FacetsResponse(category_id=category_id, filters=[], facets=[])


async def get_product_by_id(db: AsyncSession, id: uuid.UUID) -> Product:
	product = await product_crud.get_product_full(db, id)
	if not product:
		raise ProductNotFoundError("Product not found")
	return Product.model_validate(product)


async def get_similar_products(
	db: AsyncSession, id: uuid.UUID, category_id: uuid.UUID, limit: int, offset: int
) -> SimilarProductsResponse:
	if not await product_crud.get_product_full(db, id):
		raise ProductNotFoundError("Product not found")

	if not await category_crud.get_category_by_id(db, category_id):
		raise CategoryNotFoundError("Unknown category")

	products, total_count = await product_crud.get_similar_products(
		db, category_id, id, limit, offset
	)

	items = [
		ProductShort(
			id=p.id,
			title=p.title,
			image="",
			price=float(0.0),
			in_stock=False,
			is_in_cart=False,
		)
		for p in products
	]

	return SimilarProductsResponse(
		items=items, total_count=total_count, limit=limit, offset=offset
	)


def parse_deep_filters(query_params: list[tuple[str, str]]) -> dict:
	deep_filters: dict = {}
	for k, v in query_params:
		if k.startswith("filters[") and k.endswith("]"):
			inner = k[len("filters[") : -1]
			if inner in deep_filters:
				if isinstance(deep_filters[inner], list):
					deep_filters[inner].append(v)
				else:
					deep_filters[inner] = [deep_filters[inner], v]
			else:
				deep_filters[inner] = v
	return deep_filters
