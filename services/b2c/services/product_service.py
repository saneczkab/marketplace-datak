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
from services.b2b_client import request_b2b


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

	b2b_params = {"limit": limit, "offset": offset, "sort": sort}
	if category_id:
		b2b_params["category_id"] = category_id
	if q:
		b2b_params["q"] = q

	if filters_dict:
		for filter_key, filter_val in filters_dict.items():
			if isinstance(filter_val, list):
				b2b_params[f"filters[{filter_key}]"] = filter_val
			else:
				b2b_params[f"filters[{filter_key}]"] = filter_val

	b2b_data = await request_b2b("GET", "/api/v1/products", params=b2b_params)

	return ProductShortListResponse.model_validate(b2b_data)


async def get_catalog_facets_service(
	category_id: str, filters_dict: Optional[dict]
) -> dict:
	"""
	Запрашивает фасеты у B2B-сервиса с учетом текущих примененных фильтров
	"""
	b2b_params = {"category_id": category_id}

	if filters_dict:
		for filter_key, filter_val in filters_dict.items():
			b2b_params[f"filters[{filter_key}]"] = filter_val

	b2b_data = await request_b2b("GET", "/api/v1/catalog/facets", params=b2b_params)
	return b2b_data


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
