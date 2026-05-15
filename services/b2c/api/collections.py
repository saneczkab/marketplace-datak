import uuid
from typing import Annotated
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from schemas.collection import CollectionsResponse, CollectionProductsResponse
from services import collection_service

router_main = fastapi.APIRouter(prefix="/api/v1/main", tags=["Подборки"])
router_collections = fastapi.APIRouter(prefix="/api/v1/collections", tags=["Подборки"])


@router_main.get("/collections", response_model=CollectionsResponse)
async def get_collections(
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	limit: int = fastapi.Query(10, ge=1, le=50, description="Количество подборок"),
	offset: int = fastapi.Query(0, ge=0, description="Смещение"),
):
	"""
	Получить список подборок для главной страницы.
	Автоматически фильтрует неактивные и сортирует по приоритету.
	"""
	try:
		return await collection_service.get_collections_list(db_session, limit, offset)
	except fastapi.HTTPException:
		raise
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e))


@router_collections.get(
	"/{collection_id}/products", response_model=CollectionProductsResponse
)
async def get_collection_products(
	collection_id: uuid.UUID,
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	limit: int = fastapi.Query(20, ge=1, le=100),
	offset: int = fastapi.Query(0, ge=0),
):
	"""
	Получение списка товаров из конкретной подборки.
	"""
	try:
		return await collection_service.get_collection_products(
			db_session, collection_id, limit, offset
		)
	except fastapi.HTTPException:
		raise
	except Exception as e:
		# Если база каталога недоступна, по спецификации нужно отдавать 503
		raise fastapi.HTTPException(status_code=503, detail=str(e))
