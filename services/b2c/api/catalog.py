import fastapi

import uuid
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.category import FacetsResponse
from exceptions.category import CategoryNotFoundError
import services.category_service as category_service
from core import db

router = fastapi.APIRouter(prefix="/api/v1/catalog")


@router.get("/facets")
async def get_facets(
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	category_id: uuid.UUID,
	filters: str | None = None,
) -> FacetsResponse:
	try:
		return await category_service.get_category_facets(
			db_session, category_id, filters
		)
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		import traceback

		traceback.print_exc()
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
