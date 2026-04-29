import json
import uuid
from decimal import Decimal
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


async def get_products_list(
	db: AsyncSession,
	limit: int,
	offset: int,
	category_id: Optional[str],
	filters_json: Optional[str],
	sort: str,
	search: Optional[str],
) -> ProductShortListResponse:
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
				price=Decimal(0.0),
				in_stock=False,
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
			id=p.id, title=p.title, image="", price=Decimal(0.0), in_stock=False
		)
		for p in products
	]

	return SimilarProductsResponse(
		items=items, total_count=total_count, limit=limit, offset=offset
	)
