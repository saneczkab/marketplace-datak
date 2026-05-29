from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Annotated, List

from core.db import get_db
from schemas.sku import SkuCreate, SkuResponse
from services import sku as sku_service
from exceptions.sku import SkuNotFoundError
from exceptions.product import ProductNotFoundError

router = APIRouter(prefix="/skus", tags=["SKU"])


@router.post("", response_model=SkuResponse, status_code=status.HTTP_201_CREATED)
async def create_sku_endpoint(
	data: SkuCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> SkuResponse:
	"""Create a new SKU entry."""
	try:
		sku = await sku_service.create_sku(db, data.model_dump())
		return SkuResponse.model_validate(sku)
	except ProductNotFoundError as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/{sku_id}", response_model=SkuResponse)
async def update_sku_endpoint(
	sku_id: UUID,
	data: SkuCreate,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> SkuResponse:
	"""Update an existing SKU by its ID."""
	try:
		sku = await sku_service.update_sku(db, sku_id, data.model_dump())
		return SkuResponse.model_validate(sku)
	except SkuNotFoundError as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{sku_id}", response_model=SkuResponse)
async def get_sku_endpoint(
	sku_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> SkuResponse:
	"""Retrieve detailed information about a specific SKU by its unique identifier."""
	try:
		sku = await sku_service.get_sku(db, sku_id)
		return SkuResponse.model_validate(sku)
	except SkuNotFoundError as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/product/{product_id}", response_model=List[SkuResponse])
async def get_skus_by_product_endpoint(
	product_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> list[SkuResponse]:
	"""Retrieve all SKUs associated with a specific product ID."""
	skus = await sku_service.get_skus_by_product_id(db, product_id)
	return [SkuResponse.model_validate(s) for s in skus]
