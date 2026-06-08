import json
import uuid
from typing import Annotated, Optional

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from exceptions.product import (
	InvalidFilterError,
	InvalidSearchQueryError,
	InvalidSortError,
	ProductNotFoundError,
)
from exceptions.sku import SkuNotFoundError
from schemas.catalog import PaginatedCatalogProducts
from schemas.sku import Sku as SkuSchema, SkuShort as SkuShortSchema
from services import product_service, sku_service

router = fastapi.APIRouter(prefix="/api/v1/products")


@router.get("", response_model=PaginatedCatalogProducts)
async def get_product_list_api(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	category_id: Optional[uuid.UUID] = None,
	limit: int = 20,
	offset: int = 0,
	filter: Optional[str] = None,
	sort: str = "popularity",
	search: Optional[str] = None,
) -> PaginatedCatalogProducts:
	try:
		base: dict = {}
		if category_id:
			base["category_id"] = str(category_id)
		if filter:
			try:
				base.update(json.loads(filter))
			except json.JSONDecodeError as e:
				raise fastapi.HTTPException(
					status_code=400,
					detail={
						"code": "BAD_REQUEST",
						"message": "Invalid JSON in filter parameter",
					},
				) from e
		filters = product_service.parse_catalog_filters(
			query_params=[], filter_str=json.dumps(base) if base else None
		)
		return await product_service.get_products_list(
			db, limit, offset, filters, sort, search
		)
	except (InvalidSortError, InvalidSearchQueryError, InvalidFilterError) as e:
		raise fastapi.HTTPException(
			status_code=400, detail={"code": "BAD_REQUEST", "message": str(e)}
		) from e
	except Exception as e:
		raise fastapi.HTTPException(
			status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(e)}
		) from e


@router.get("/{product_id}/skus/{sku_id}", response_model=SkuSchema)
async def get_sku_by_id_api(
	sku_id: uuid.UUID,
	product_id: uuid.UUID,  # noqa
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> SkuSchema:
	"""
	API endpoint for getting a sku by id
	:param sku_id: SKU ID
	:param product_id: product ID
	:param db: database session
	:return: SKU
	"""
	try:
		sku = await sku_service.get_sku_by_id(db, sku_id)
		return SkuSchema.model_validate(sku)
	except SkuNotFoundError as err:
		raise fastapi.HTTPException(
			status_code=404, detail={"code": "NOT_FOUND", "message": str(err)}
		) from err


@router.get("/{product_id}/skus", response_model=list[SkuShortSchema])
async def get_product_skus_short_api(
	product_id: uuid.UUID,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> list[SkuShortSchema]:
	"""
	API endpoint for getting a SKUs by product ID
	:param product_id: product ID
	:param db: database session
	:return: SKUs short
	"""
	try:
		skus = await product_service.get_product_skus_short(db, product_id)
		skus_validated = (SkuShortSchema.model_validate(sku) for sku in skus)
		return list(skus_validated)
	except ProductNotFoundError as err:
		raise fastapi.HTTPException(
			status_code=404, detail={"code": "NOT_FOUND", "message": str(err)}
		) from err
