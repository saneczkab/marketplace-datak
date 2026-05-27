from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from schemas.product import (
	ProductCreate,
	ProductResponse,
	ProductUpdate,
	ProductSellerRead,
)
from services import product_service
from uuid import UUID
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/products", tags=["B2B Products"])
security = HTTPBearer()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
	product_in: ProductCreate,
	db: Annotated[AsyncSession, Depends(get_db)],
	credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> ProductSellerRead:
	seller_id = credentials.credentials
	try:
		return await product_service.create_new_product(db, product_in, seller_id)
	except ValidationError as e:
		raise HTTPException(status_code=422, detail=f"{e}") from e
	except Exception as e:
		raise HTTPException(status_code=418, detail=f"{e}") from e


@router.get("/", response_model=list[ProductSellerRead])
async def get_my_products(
	db: Annotated[AsyncSession, Depends(get_db)],
	seller_id: UUID,
) -> list[ProductSellerRead]:
	return await product_service.get_all_seller_products(db, seller_id)


@router.get("/{product_id}", response_model=ProductSellerRead)
async def get_product(
	product_id: UUID,
	db: Annotated[AsyncSession, Depends(get_db)],
	seller_id: UUID,
) -> ProductSellerRead:
	return await product_service.get_product_for_seller(db, product_id, seller_id)


@router.patch("/{product_id}", response_model=ProductSellerRead)
async def patch_product(
	product_id: UUID,
	product_in: ProductUpdate,
	db: Annotated[AsyncSession, Depends(get_db)],
	seller_id: UUID,
) -> ProductSellerRead:
	return await product_service.patch_existing_product(
		db, product_id, seller_id, product_in
	)


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
	product_id: UUID,
	db: Annotated[AsyncSession, Depends(get_db)],
	seller_id: UUID,
) -> dict[str, str]:
	return await product_service.remove_product(db, product_id, seller_id)
