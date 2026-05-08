import uuid
from typing import Annotated, Optional

import fastapi
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from exceptions.favorite import InvalidParameterError
from exceptions.product import ProductNotFoundError
from schemas.favorite import FavoriteMutationResponse, FavoritesResponse
from services import favorite_service

router = fastapi.APIRouter(prefix="/api/v1/favorites", tags=["Избранное"])


@router.get(
	"",
	response_model=FavoritesResponse,
	responses={200: {}, 400: {}, 401: {}, 503: {}},
)
async def get_favorites(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	user_id: Annotated[uuid.UUID, fastapi.Query()],
	limit: Annotated[int, fastapi.Query(ge=1, le=100)] = 20,
	offset: Annotated[int, fastapi.Query(ge=0)] = 0,
	authorization: Annotated[Optional[str], fastapi.Header()] = None,
) -> FavoritesResponse:
	_ = authorization
	try:
		return await favorite_service.get_favorites_list(db, user_id, limit, offset)
	except InvalidParameterError as err:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "INVALID_PARAMETER", "message": str(err)},
		) from None


@router.post(
	"/{product_id}",
	responses={
		200: {"model": FavoriteMutationResponse},
		201: {"model": FavoriteMutationResponse},
		400: {},
		401: {},
		404: {},
		503: {},
	},
)
async def add_to_favorites(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	product_id: Annotated[uuid.UUID, fastapi.Path()],
	user_id: Annotated[uuid.UUID, fastapi.Query()],
	authorization: Annotated[Optional[str], fastapi.Header()] = None,
) -> JSONResponse:
	_ = authorization
	try:
		result = await favorite_service.add_to_favorites(db, user_id, product_id)

		response = FavoriteMutationResponse(
			product_id=result["favorite"].product_id,
			user_id=result["favorite"].user_id,
			added_at=result["favorite"].added_at,
			message="Товар уже находится в избранном"
			if not result["is_new"]
			else "Товар добавлен в избранное",
		)

		return JSONResponse(
			status_code=201 if result["is_new"] else 200,
			content=response.model_dump(mode="json"),
		)
	except ProductNotFoundError as err:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "PRODUCT_NOT_FOUND", "message": str(err)},
		) from None
	except InvalidParameterError as err:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "INVALID_PARAMETER", "message": str(err)},
		) from None


@router.delete(
	"/{product_id}",
	status_code=204,
	responses={204: {}, 400: {}, 401: {}, 404: {}, 503: {}},
)
async def remove_from_favorites(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	product_id: Annotated[uuid.UUID, fastapi.Path()],
	user_id: Annotated[uuid.UUID, fastapi.Query()],
	authorization: Annotated[Optional[str], fastapi.Header()] = None,
) -> None:
	_ = authorization
	try:
		await favorite_service.remove_from_favorites(db, user_id, product_id)
	except ProductNotFoundError as err:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "PRODUCT_NOT_FOUND", "message": str(err)},
		) from None
	except InvalidParameterError as err:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "INVALID_PARAMETER", "message": str(err)},
		) from None
