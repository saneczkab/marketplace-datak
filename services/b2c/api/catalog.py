import fastapi

import uuid
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
import json

from exceptions.banner import BannerNotFoundError, EmptyEventsError
from schemas.banner import Banner, BannerEventsRequest
from schemas.category import FacetsResponse
from exceptions.category import CategoryNotFoundError
from core import db


from services import category_service, banner_service
from core.db import get_db

router = fastapi.APIRouter(prefix="/api/v1/catalog")


# @router.get("/facets")
async def get_facets(
	request: Request,
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	category_id: uuid.UUID,
	filters: str | None = None,
) -> FacetsResponse:
	try:
		qp = request.query_params
		deep: dict = {}
		for k, v in qp.multi_items():
			if k.startswith("filters[") and k.endswith("]"):
				inner = k[len("filters[") : -1]
				if inner in deep:
					if isinstance(deep[inner], list):
						deep[inner].append(v)
					else:
						deep[inner] = [deep[inner], v]
				else:
					deep[inner] = v

		filters_param = json.dumps(deep, ensure_ascii=False) if deep else filters

		return await category_service.get_category_facets(
			db_session, category_id, filters_param
		)
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		import traceback

		traceback.print_exc()
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


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
			status_code=404,
			detail={"code": "BANNER_NOT_FOUND", "message": str(e)},
		) from e
	return fastapi.Response(status_code=204)
