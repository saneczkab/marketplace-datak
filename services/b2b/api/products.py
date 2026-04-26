from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from schemas.product import ProductCreate, ProductUpdate, ProductSellerRead
from services import product_service
from uuid import UUID
from schemas.product import ProductStatusUpdate


router = APIRouter(prefix="/products", tags=["B2B Products"])


@router.post("/", response_model=ProductSellerRead, status_code=status.HTTP_201_CREATED)
async def create_product(
	product_in: ProductCreate,
	db: AsyncSession = Depends(get_db),
	seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
	return await product_service.create_new_product(db, product_in, seller_id)


@router.get("/", response_model=list[ProductSellerRead])
async def get_my_products(
	db: AsyncSession = Depends(get_db),
	seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
	return await product_service.get_all_seller_products(db, seller_id)


@router.get("/{product_id}", response_model=ProductSellerRead)
async def get_product(
	product_id: UUID,
	db: AsyncSession = Depends(get_db),
	seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
	return await product_service.get_product_for_seller(db, product_id, seller_id)


@router.patch("/{product_id}", response_model=ProductSellerRead)
async def patch_product(
	product_id: UUID,
	product_in: ProductUpdate,
	db: AsyncSession = Depends(get_db),
	seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
	return await product_service.patch_existing_product(
		db, product_id, seller_id, product_in
	)


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
	product_id: UUID,
	db: AsyncSession = Depends(get_db),
	seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
	return await product_service.remove_product(db, product_id, seller_id)


@router.patch("/{product_id}/status", response_model=ProductSellerRead)
async def update_product_status(
	product_id: UUID,
	status_data: ProductStatusUpdate,
	db: AsyncSession = Depends(get_db),
	seller_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
	return await product_service.change_product_status(
		db, product_id, seller_id, status_data.status
	)
