from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

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
def create_sku_endpoint(
    data: SkuCreate,
    db: Session = Depends(get_db),
):
    return create_sku(db, data.dict())

@router.put("/{sku_id}", response_model=SkuResponse)
def update_sku_endpoint(
    sku_id: UUID,
    data: SkuCreate,
    db: Session = Depends(get_db),
):
    sku = update_sku(db, sku_id, data.dict())

    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    return sku

@router.get("/{sku_id}", response_model=SkuResponse)
def get_sku_endpoint(
    sku_id: UUID,
    db: Session = Depends(get_db),
):
    sku = get_sku(db, sku_id)

    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    return sku

@router.get("/product/{product_id}")
def get_skus_by_product_endpoint(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    return get_skus_by_product(db, product_id)
