import uuid
from typing import Annotated, Optional

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from exceptions.product import InvalidFiltersError, ProductNotFoundError, SearchQueryTooShortError
from exceptions.sku import SkuNotFoundError
from schemas.product import ProductCard, ProductShortListResponse
from schemas.sku import Sku as SkuSchema, SkuShort as SkuShortSchema
from services import product_service, sku_service

router = fastapi.APIRouter(prefix="/api/v1/products")


@router.get("", response_model=ProductShortListResponse)
async def get_product_list_api(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	category_id: Optional[uuid.UUID] = None,
	limit: int = 20,
	offset: int = 0,
	filter: Optional[str] = None,
	sort: str = "popularity",
	search: Optional[str] = None,
) -> ProductShortListResponse:
	try:
		return await product_service.get_products_list(
			db,
			limit,
			offset,
			str(category_id) if category_id else None,
			filter,
			sort,
			search,
		)
	except (InvalidFiltersError, SearchQueryTooShortError, ValueError) as e:
		raise fastapi.HTTPException(status_code=400, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e


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
		raise fastapi.HTTPException(status_code=404, detail=str(err)) from err


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
		raise fastapi.HTTPException(status_code=404, detail=str(err)) from err


@router.get("/{id}", response_model=ProductCard)
async def get_product_api(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)], id: uuid.UUID
) -> ProductCard:
	try:
		return await product_service.get_product_by_id(db, id)
	except ProductNotFoundError as err:
		raise fastapi.HTTPException(status_code=404, detail=str(err)) from err
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e
