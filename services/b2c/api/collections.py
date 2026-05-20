import uuid
from typing import Annotated

import fastapi
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from schemas.collection import CollectionsResponse, CollectionProductsResponse
from services import collection_service
from exceptions.collection import CollectionNotFoundError

router_main = fastapi.APIRouter(prefix="/api/v1/main", tags=["Подборки"])
router_collections = fastapi.APIRouter(prefix="/api/v1/collections", tags=["Подборки"])


@router_main.get("/collections", response_model=CollectionsResponse)
async def get_collections(
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	limit: Annotated[int, Query(default=20, ge=1, le=100)],
	offset: Annotated[int, Query(default=0, ge=0)],
) -> CollectionsResponse:
	try:
		return await collection_service.get_collections_list(db_session, limit, offset)
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e


@router_collections.get(
	"/{collection_id}/products", response_model=CollectionProductsResponse
)
async def get_collection_products(
	collection_id: uuid.UUID,
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	limit: Annotated[int, Query(default=20, ge=1, le=100)],
	offset: Annotated[int, Query(default=0, ge=0)],
) -> CollectionProductsResponse:
	try:
		return await collection_service.get_collection_products(
			db_session, collection_id, limit, offset
		)
	except CollectionNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404, detail={"code": "COLLECTION_NOT_FOUND", "message": str(e)}
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
