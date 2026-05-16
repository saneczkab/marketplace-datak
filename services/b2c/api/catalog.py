import fastapi

import uuid
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
import json

from schemas.category import FacetsResponse
from exceptions.category import CategoryNotFoundError
import services.category_service as category_service
from core import db

router = fastapi.APIRouter(prefix="/api/v1/catalog")


@router.get("/facets")
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
