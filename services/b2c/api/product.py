from typing import Annotated
import uuid

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from exceptions.sku import SkuNotFoundError
from schemas.sku import Sku
from services import sku_service

router = fastapi.APIRouter(prefix="/api/v1/products")


@router.get("/{product_id}/skus/{sku_id}", response_model=Sku)
async def get_sku_by_id_api(
	sku_id: uuid.UUID,
	product_id: uuid.UUID,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> Sku:
	try:
		sku = await sku_service.get_sku_by_id(db, sku_id)
		return Sku.model_validate(sku)
	except SkuNotFoundError as err:
		raise fastapi.HTTPException(status_code=404, detail=str(err)) from err
