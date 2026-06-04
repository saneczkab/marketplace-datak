import uuid
import json
from json import JSONDecodeError
from pydantic import ValidationError
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

import crud.product as product_crud
import crud.category as category_crud
import crud.review as review_crud
from database.models import Sku
from exceptions.product import (
	ProductNotFoundError,
	InvalidSortError,
	InvalidSearchQueryError,
	InvalidFilterError,
)
from schemas.catalog import CatalogProductCard, PaginatedCatalogProducts
from schemas.product import (
	Product,
	ProductFilterParams,
)
from services.schemas_builder import build_catalog_product_cards
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
	filters: ProductFilterParams,
	sort: str,
	q: Optional[str],
) -> PaginatedCatalogProducts:
	valid_sorts = [
		"price_asc",
		"price_desc",
		"popularity",
		"new",
	]
	if sort not in valid_sorts:
		raise InvalidSortError(
			f"Invalid sort parameter. Allowed: {', '.join(valid_sorts)}"
		)

	if q:
		search_stripped = q.strip()
		if 0 < len(search_stripped) <= 3:
			raise InvalidSearchQueryError("Search query must be at least 3 characters")
		if len(search_stripped) > 255:
			raise InvalidSearchQueryError("Search query must be at most 255 characters")

	category_id = filters.category_id

	crud_filters = {}
	if filters.seller_id:
		crud_filters["seller_id"] = filters.seller_id
	if filters.price_min is not None:
		crud_filters["price_min"] = filters.price_min
	if filters.price_max is not None:
		crud_filters["price_max"] = filters.price_max
	if filters.attributes:
		crud_filters["attributes"] = filters.attributes

	products, total = await product_crud.get_products_list(
		db=db,
		limit=limit,
		offset=offset,
		category_id=category_id,
		filter=crud_filters if crud_filters else None,
		sort=sort,
		q=q,
	)

	if not products:
		return PaginatedCatalogProducts(
			items=[], total_count=total, limit=limit, offset=offset
		)

	categories_map = await category_crud.get_all_categories_map(db)
	review_stats_by_product = await review_crud.get_reviews_stats_by_product_ids(
		db, [product.id for product in products]
	)

	catalog_cards = build_catalog_product_cards(
		products, categories_map, review_stats_by_product
	)

	return PaginatedCatalogProducts(
		items=catalog_cards, total_count=total, limit=limit, offset=offset
	)


async def get_catalog_facets_service(
	db: AsyncSession,  # noqa
	category_id: str,
	raw_query_params: list[tuple[str, str]],  # noqa
) -> FacetsResponse:
	str_category_id = str(category_id)

	return FacetsResponse(category_id=str_category_id, filters=[], facets=[])


async def get_product_by_id(db: AsyncSession, id: uuid.UUID) -> Product:
	product = await product_crud.get_product_full(db, id)
	if not product:
		raise ProductNotFoundError("Product not found")
	return Product.model_validate(product)


async def get_similar_products(
	db: AsyncSession, product_id: uuid.UUID, limit: int
) -> list[CatalogProductCard]:
	category_id = await product_crud.get_product_category_id(db, product_id)
	products = await product_crud.get_similar_products(
		db, category_id, product_id, limit
	)
	if not products:
		return []

	categories_map = await category_crud.get_all_categories_map(db)
	review_stats_by_product = await review_crud.get_reviews_stats_by_product_ids(
		db, [product.id for product in products]
	)
	return build_catalog_product_cards(
		products, categories_map, review_stats_by_product
	)


def _assign_nested_value(target: dict, path: list[str], value: str) -> None:
	current = target
	for key in path[:-1]:
		if key not in current or not isinstance(current[key], dict):
			current[key] = {}
		current = current[key]
	final_key = path[-1]
	if final_key in current:
		if isinstance(current[final_key], list):
			current[final_key].append(value)
		else:
			current[final_key] = [current[final_key], value]
	else:
		current[final_key] = value


def parse_deep_filters(query_params: list[tuple[str, str]]) -> dict:
	deep_filters: dict = {}
	for k, v in query_params:
		if not k.startswith("filter[") or not k.endswith("]"):
			continue
		inner = k[len("filter[") : -1]
		path = inner.split("][")
		_assign_nested_value(deep_filters, path, v)
	return deep_filters


def parse_catalog_filters(
	query_params: list[tuple[str, str]], filter_str: Optional[str] = None
) -> ProductFilterParams:
	parsed_filters = parse_deep_filters(query_params)

	if filter_str:
		try:
			parsed_json = (
				json.loads(filter_str) if isinstance(filter_str, str) else filter_str
			)
			if not isinstance(parsed_json, dict):
				raise InvalidFilterError("Invalid filter format or schema parameters")
			parsed_filters.update(parsed_json)
		except (JSONDecodeError, ValidationError) as e:
			raise InvalidFilterError(
				"Invalid filter format or schema parameters"
			) from e

	if parsed_filters:
		try:
			return ProductFilterParams.model_validate(parsed_filters)
		except ValidationError as e:
			raise InvalidFilterError(
				"Invalid filter format or schema parameters"
			) from e

	return ProductFilterParams()
