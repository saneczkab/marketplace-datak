import fastapi

import uuid

from schemas.category import FacetsResponse
from exceptions.category import CategoryNotFoundError
import services.category_service as category_service

router = fastapi.APIRouter(prefix="/api/v1/catalog")


@router.get("/facets")
async def get_facets(category_id: uuid.UUID, filters: str | None = None) -> FacetsResponse:
	try:
		return await category_service.get_category_facets(category_id, filters)
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
