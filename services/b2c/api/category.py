import fastapi
from typing import Annotated
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from services import category_service
from core import db


router = fastapi.APIRouter(prefix="/api/v1/categories")


@router.get("/")
async def list_categories(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> str:
	try:
		return JSONResponse(content=await category_service.get_categories_tree(db))
	except category_service.category_exceptions.CategoryNotFoundError as err:
		raise fastapi.HTTPException(status_code=404, detail=str(err)) from err


@router.get("/{category_id}")
async def get_category(
	category_id: str,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> str:
	try:
		return await category_service.get_category_info_by_id(
			db, category_id, need_count=True
		)
	except category_service.category_exceptions.CategoryNotFoundError as err:
		raise fastapi.HTTPException(status_code=404, detail=str(err)) from err
