from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from database.core import get_db
from schemas.sku import SkuCreate, SkuResponse
from services.sku import (
    create_sku,
    update_sku,
    get_sku,
    get_skus_by_product,
)

router = APIRouter(prefix="/api/v1/skus", tags=["SKU"])


@router.post("", response_model=SkuResponse)
async def create_sku_endpoint(
    data: SkuCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_sku(db, data.model_dump()) 

@router.put("/{sku_id}", response_model=SkuResponse)
async def update_sku_endpoint(
    sku_id: UUID,
    data: SkuCreate,
    db: AsyncSession = Depends(get_db),
):
    sku = await update_sku(db, sku_id, data.model_dump())

    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    return sku

@router.get("/{sku_id}", response_model=SkuResponse)
async def get_sku_endpoint(
    sku_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    sku = await get_sku(db, sku_id)

    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    return sku

@router.get("/product/{product_id}", response_model=List[SkuResponse])
async def get_skus_by_product_endpoint(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await get_skus_by_product(db, product_id)