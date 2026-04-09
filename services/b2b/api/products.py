from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from schemas.product import ProductCreate, ProductSellerRead
from services import product_service
from uuid import UUID


router = APIRouter(prefix="/products", tags=["B2B Products"])

@router.post("/", response_model=ProductSellerRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    # В будущем тут будет current_seller = Depends(get_current_seller)
    # Пока для тестов используем заглушку seller_id
    seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000")
):
    return await product_service.create_new_product(db, product_in, seller_id)

@router.get("/", response_model=list[ProductSellerRead])
async def get_my_products(
    db: AsyncSession = Depends(get_db),
    seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000")
):
    return await product_service.get_all_seller_products(db, seller_id)

@router.get("/{product_id}", response_model=ProductSellerRead)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000")
):
    return await product_service.get_product_for_seller(db, product_id, seller_id)