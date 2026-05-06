import json
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

import crud.product as product_crud
from database.models import Sku
from exceptions.product import ProductNotFoundError
from schemas.product import (
	ProductShort,
	Product,
	ProductShortListResponse,
	SimilarProductsResponse,
)
from schemas.sku import SkuShort
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
	filters_json: Optional[str],
	sort: str,
	search: Optional[str],
) -> ProductShortListResponse:
	# Валидация sort согласно спецификации
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

	# Валидация search - минимум 4 символа (после trim)
	if search and len(search.strip()) > 0 and len(search.strip()) < 4:
		raise ValueError("Search query must be at least 3 characters")
	
	# Экранирование от символов %, _, ' 
	if search:
		search = search.replace("%", "\\%").replace("_", "\\_").replace("'", "''")

	cat_uuid = uuid.UUID(category_id) if category_id else None
	filters = json.loads(filters_json) if filters_json else {}

	products, total_count = await product_crud.get_products_list(
		db, limit, offset, cat_uuid, filters, sort, search
	)

	items = []
	for p in products:
		main_image_url = p.images[0].url if p.images else ""
		items.append(
			ProductShort(
				id=p.id,
				title=p.title,
				image=main_image_url,
				price=float(0.0),
				in_stock=False,
				is_in_cart=False,
			)
		)

	return ProductShortListResponse(
		items=items, total_count=total_count, limit=limit, offset=offset
	)


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
