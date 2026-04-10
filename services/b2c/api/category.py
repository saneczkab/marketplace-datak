import fastapi

from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.category import CategoryInfoResponse, CategoryTreeResponse
from exceptions.category import CategoryNotFoundError
import services.category_service as category_service

from core import db

router = fastapi.APIRouter(prefix="/api/v1/categories")

@router.get("/{id}")
async def get_category_info(db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],id: str) -> CategoryInfoResponse:
	try:
		return await category_service.get_category_info(db, id)
	except ValueError as e:
		raise fastapi.HTTPException(status_code=400, detail="id must be a valid UUID") from e
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
	

@router.get("")
async def get_categories_tree(db: Annotated[AsyncSession, fastapi.Depends(db.get_db)]) -> CategoryTreeResponse:
	return await category_service.get_categories_tree(db)

