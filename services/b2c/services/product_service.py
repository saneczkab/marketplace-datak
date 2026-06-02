import json
import uuid
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

import crud.product as product_crud
import crud.category as category_crud
import crud.review as review_crud
from database.models import Sku, ProductStatusEnum
from exceptions.product import (
	InvalidFiltersError,
	ProductNotFoundError,
	SearchQueryTooShortError,
)
from schemas.catalog import CatalogProductCard
from schemas.product import (
	ProductShort,
	ProductShortListResponse,
	ProductCard,
	ProductCardImage,
	ProductCardSku,
	ProductCardCharacteristic,
)
from services.schemas_builder import build_catalog_product_cards
from schemas.sku import SkuShort
from schemas.sku import Sku as SkuSchema
from schemas.image import Image


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
	filters_raw: Optional[str],
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
		raise ValueError(f"Invalid sort parameter. Allowed: {', '.join(valid_sorts)}")

	if q:
		search_stripped = q.strip()

		if 0 < len(search_stripped) < 4:
			raise SearchQueryTooShortError("Search query must be at least 3 characters")

		if len(search_stripped) > 255:
			raise ValueError("Search query must be at most 255 characters")

	cat_uuid = uuid.UUID(category_id) if category_id else None
	try:
		filter = json.loads(filters_raw) if filters_raw else {}
	except json.JSONDecodeError as e:
		raise InvalidFiltersError("Invalid JSON in filters parameter") from e

	products, total_count = await product_crud.get_products_list(
		db, limit, offset, cat_uuid, filter, sort, q
	)

	items = []
	for p in products:
		main_image_url = p.images[0].url if p.images else ""

		# SKU is used to determine price
		skus: List[SkuSchema] = await product_crud.get_product_skus(db, p.id)
		price = min((sku.price for sku in skus), default=0.0) if skus else 0.0

		items.append(
			ProductShort(
				id=p.id,
				title=p.title,
				image=main_image_url,
				price=float(price),
				in_stock=False,
				is_in_cart=False,
			)
		)

	return ProductShortListResponse(
		items=items, total_count=total_count, limit=limit, offset=offset
	)


async def get_product_by_id(db: AsyncSession, id: uuid.UUID) -> ProductCard:
	product = await product_crud.get_product_full(db, id)
	if not product:
		raise ProductNotFoundError("Product not found")
	if product.status != ProductStatusEnum.MODERATED or product.deleted:
		raise ProductNotFoundError("Product not found")

	images = sorted(product.images or [], key=lambda img: img.ordering)
	characteristics = [
		ProductCardCharacteristic(name=c.name, value=c.value)
		for c in (product.characteristics or [])
	]
	skus = [
		ProductCardSku(
			id=sku.id,
			name=sku.name,
			price=sku.price,
			discount=sku.discount,
			active_quantity=sku.active_quantity,
			in_stock=sku.active_quantity > 0,
			image=sku.images[0].url if sku.images else None,
			characteristics=[
				ProductCardCharacteristic(name=c.name, value=c.value)
				for c in (sku.characteristics or [])
			],
		)
		for sku in (product.skus or [])
	]

	return ProductCard(
		id=product.id,
		slug=product.slug,
		title=product.title,
		description=product.description,
		images=[ProductCardImage(url=img.url, ordering=img.ordering) for img in images],
		status=product.status,
		characteristics=characteristics,
		skus=skus,
	)


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
