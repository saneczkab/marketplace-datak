from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.seller import SellerNotFoundError
from schemas.seller import SellerInfoPatch, SellerInfoResponse
from services import seller_service

router = APIRouter(prefix="/sellers", tags=["Seller"])


@router.get("/{seller_id}")
async def get_seller_info(
	db: Annotated[AsyncSession, Depends(get_db)], seller_id: UUID
) -> SellerInfoResponse:
	try:
		return await seller_service.get_seller_info(db, seller_id)
	except SellerNotFoundError as e:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND_ERROR", "message": f"seller {id} not found"},
		) from e
	except Exception as e:
		raise HTTPException(
			status_code=500,
			detail={"code": "INTERNAL_ERROR", "message": e},
		) from e


@router.patch("/{seller_id}")
async def patch_seller_info(
	db: Annotated[AsyncSession, Depends(get_db)], seller_id: UUID, data: SellerInfoPatch
) -> SellerInfoResponse:
	try:
		return await seller_service.update_seller(db, data, seller_id)
	except Exception as e:
		raise HTTPException(
			status_code=500,
			detail={"code": "INTERNAL_ERROR", "message": e},
		) from e
