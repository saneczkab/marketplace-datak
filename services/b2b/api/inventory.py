from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.inventory import (
	FulfillConflictError,
	InventoryValidationError,
	ReserveConflictError,
	UnreserveConflictError,
)
from exceptions.sku import SkuNotFoundError
from schemas.inventory import (
	InventoryOrderRequest,
	InventoryOrderResponse,
	ReserveRequest,
	ReserveResponse,
)
from services import inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/reserve", response_model=ReserveResponse)
async def reserve_inventory_endpoint(
	request: ReserveRequest,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> ReserveResponse:
	try:
		return await inventory_service.reserve_inventory(db, request)
	except SkuNotFoundError as e:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except ReserveConflictError as e:
		raise HTTPException(
			status_code=409,
			detail={
				"code": "INSUFFICIENT_STOCK",
				"message": str(e),
				"details": {"failed_items": e.failed_items},
			},
		) from e
	except InventoryValidationError as e:
		raise HTTPException(
			status_code=422,
			detail={"code": "VALIDATION_ERROR", "message": str(e)},
		) from e


@router.post("/unreserve", response_model=InventoryOrderResponse)
async def unreserve_inventory_endpoint(
	request: InventoryOrderRequest,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> InventoryOrderResponse:
	try:
		return await inventory_service.unreserve_inventory(db, request)
	except SkuNotFoundError as e:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except UnreserveConflictError as e:
		raise HTTPException(
			status_code=409,
			detail={"code": "CONFLICT", "message": str(e)},
		) from e
	except InventoryValidationError as e:
		raise HTTPException(
			status_code=422,
			detail={"code": "VALIDATION_ERROR", "message": str(e)},
		) from e


@router.post("/fulfill", response_model=InventoryOrderResponse)
async def fulfill_inventory_endpoint(
	request: InventoryOrderRequest,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> InventoryOrderResponse:
	try:
		return await inventory_service.fulfill_inventory(db, request)
	except SkuNotFoundError as e:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except FulfillConflictError as e:
		raise HTTPException(
			status_code=409,
			detail={"code": "CONFLICT", "message": str(e)},
		) from e
	except InventoryValidationError as e:
		raise HTTPException(
			status_code=422,
			detail={"code": "VALIDATION_ERROR", "message": str(e)},
		) from e
