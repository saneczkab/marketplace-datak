from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.inventory import FulfillConflictError, InventoryValidationError
from exceptions.sku import SkuNotFoundError
from schemas.inventory import FulfillRequest, FulfillResponse
from services import inventory_service

router = APIRouter(tags=["Inventory"])


@router.post("/fulfill", response_model=FulfillResponse)
async def fulfill_inventory_endpoint(
	request: FulfillRequest,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> FulfillResponse:
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
