import fastapi

import uuid
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from exceptions.banner import BannerNotFoundError, EmptyEventsError
from exceptions.product import InvalidSortError, InvalidSearchQueryError
from schemas.banner import Banner, BannerEventsRequest
from schemas.category import FacetsResponse
from core import db


from schemas.collection import Collection
from schemas.product import ProductShortListResponse
from services.b2b_client import B2BServiceUnavailableError, B2BNotFoundError
from services import (
	banner_service,
	collection_service,
	product_service,
)
from core.db import get_db

router = fastapi.APIRouter(prefix="/api/v1/catalog")


@router.get("/facets", response_model=FacetsResponse)
async def get_facets(
	request: Request,
	category_id: uuid.UUID,
) -> FacetsResponse:
	try:
		deep: dict = {}
		for k, v in request.query_params.multi_items():
			if k.startswith("filters[") and k.endswith("]"):
				inner = k[len("filters[") : -1]
				if inner in deep:
					if isinstance(deep[inner], list):
						deep[inner].append(v)
					else:
						deep[inner] = [deep[inner], v]
				else:
					deep[inner] = v

		facets_data = await product_service.get_catalog_facets_service(
			str(category_id), deep
		)
		return FacetsResponse.model_validate(facets_data)

	except B2BNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail="Category not found") from e
	except B2BServiceUnavailableError as e:
		raise fastapi.HTTPException(
			status_code=502, detail="Catalog temporarily unavailable"
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/collections", response_model=list[Collection])
async def get_collections(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
) -> list[Collection]:
	return await collection_service.get_catalog_collections(db)


@router.get("/banners")
async def get_banners(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
) -> list[Banner]:
	"""Get active banners

	Args:
		db (Annotated[AsyncSession, fastapi.Depends]): Database session

	Returns:
		list[Banner]: List of active banners
	"""
	return await banner_service.get_active_banners(db)


@router.post("/banner-events", status_code=204)
async def post_banner_events(
	request: Request,
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
	body: BannerEventsRequest,
) -> fastapi.Response:
	user_id = getattr(request.state, "user_id", None)
	try:
		await banner_service.record_banner_events(db, body, user_id)
	except EmptyEventsError as e:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "EMPTY_EVENTS", "message": str(e)},
		) from e
	except BannerNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "BANNER_NOT_FOUND", "message": str(e)},
		) from e
	return fastapi.Response(status_code=204)


@router.get("/products", response_model=ProductShortListResponse)
async def get_product_list_api(
	request: Request,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	category_id: Optional[uuid.UUID] = None,
	limit: int = 20,
	offset: int = 0,
	sort: str = "rating",
	q: Optional[str] = None,
) -> ProductShortListResponse:
	deep_filters: dict = {}
	for k, v in request.query_params.multi_items():
		if k.startswith("filters[") and k.endswith("]"):
			inner = k[len("filters[") : -1]
			if inner in deep_filters:
				if isinstance(deep_filters[inner], list):
					deep_filters[inner].append(v)
				else:
					deep_filters[inner] = [deep_filters[inner], v]
			else:
				deep_filters[inner] = v

	try:
		return await product_service.get_products_list(
			db,
			limit,
			offset,
			str(category_id) if category_id else None,
			deep_filters,
			sort,
			q,
		)
	except (InvalidSortError, InvalidSearchQueryError) as e:
		raise fastapi.HTTPException(
			status_code=400, detail={"code": "INVALID_REQUEST", "message": str(e)}
		) from e
	except B2BNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail="Category not found") from e
	except B2BServiceUnavailableError as e:
		raise fastapi.HTTPException(
			status_code=502, detail="Catalog temporarily unavailable"
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e
