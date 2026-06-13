import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.product import (
	ProductAlreadyDeletedError,
	ProductForbiddenError,
	ProductNotFoundError,
	ProductNotOwnerError,
)
from database.models import ProductStatusEnum
from schemas.product import (
	ProductCreate,
	ProductDetailResponse,
	ProductResponse,
	ProductSellerListResponse,
	ProductUpdate,
	SellerProductStatusFilter,
)
from services import product_service

security = HTTPBearer()
router = APIRouter(
	prefix="/products",
	tags=["B2B Products"],
	dependencies=[Depends(security)],
)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
	product_in: ProductCreate,
	db: Annotated[AsyncSession, Depends(get_db)],
	credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> ProductResponse:
	seller_id = credentials.credentials
	try:
		return await product_service.create_new_product(db, product_in, seller_id)
	except ValidationError as e:
		raise HTTPException(
			status_code=422,
			detail={"code": "VALIDATION_ERROR", "message": "Request validation failed"},
		) from e
	except Exception as e:
		raise HTTPException(
			status_code=500,
			detail={"code": "INTERNAL_ERROR", "message": "Internal server error"},
		) from e


@router.get("", response_model=ProductSellerListResponse)
async def get_my_products(
	request: Request,
	db: Annotated[AsyncSession, Depends(get_db)],
	limit: Annotated[int, Query(ge=1, le=100)] = 20,
	offset: Annotated[int, Query(ge=0)] = 0,
	status_filter: Annotated[
		SellerProductStatusFilter | None, Query(alias="status")
	] = None,
	search: str | None = None,
	include_deleted: Annotated[bool, Query()] = False,
) -> ProductSellerListResponse:
	seller_id = uuid.UUID(str(getattr(request.state, "user_id", None)))
	status_arg = ProductStatusEnum(status_filter.value) if status_filter else None
	return await product_service.list_seller_products(
		db, seller_id, limit, offset, status_arg, search, include_deleted
	)


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
	request: Request,
	product_id: UUID,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductDetailResponse:
	seller_id = uuid.UUID(str(getattr(request.state, "user_id", None)))
	try:
		return await product_service.get_product_for_seller(db, product_id, seller_id)
	except ProductNotFoundError as e:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e


@router.patch("/{product_id}", response_model=ProductResponse)
async def patch_product(
	request: Request,
	product_id: UUID,
	product_in: ProductUpdate,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductResponse:
	seller_id = uuid.UUID(str(getattr(request.state, "user_id", None)))
	try:
		return await product_service.patch_existing_product(
			db, product_id, seller_id, product_in
		)
	except ProductNotFoundError as e:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except ProductNotOwnerError as e:
		raise HTTPException(
			status_code=403,
			detail={"code": "NOT_OWNER", "message": str(e)},
		) from e
	except ProductForbiddenError as e:
		raise HTTPException(
			status_code=403,
			detail={"code": "FORBIDDEN", "message": str(e)},
		) from e


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
	request: Request,
	product_id: UUID,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
	seller_id = uuid.UUID(str(getattr(request.state, "user_id", None)))
	try:
		await product_service.remove_product(db, product_id, seller_id)
	except (ProductNotFoundError, ProductAlreadyDeletedError) as e:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except ProductNotOwnerError as e:
		raise HTTPException(
			status_code=403,
			detail={"code": "NOT_OWNER", "message": str(e)},
		) from e
