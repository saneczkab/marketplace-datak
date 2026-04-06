import fastapi
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from services import category_service
from core import db

router = fastapi.APIRouter(prefix="/api/v1/categories")

@router.get("/")
async def list_categories(db: Annotated[AsyncSession, fastapi.Depends(db.get_db)]) -> str:
    try:
        return await category_service.get_categories_tree(db)
    except category_service.category_exceptions.CategoryNotFoundError as err:
        raise fastapi.HTTPException(status_code=404, detail=str(err)) from err
    