import fastapi

from schemas.category import BreadcrumbResponse
from exceptions.category import CategoryNotFoundError
from services import category_service

router = fastapi.APIRouter(prefix="/api/v1/breadcrumbs")


@router.get("/{category_id}")
async def get_breadcrumbs(
	category_id: str | None, product_id: str | None
) -> BreadcrumbResponse:
	try:
		return await category_service.get_category_breadcrumbs(category_id, product_id)
	except ValueError as e:
		raise fastapi.HTTPException(
			status_code=400, detail="Either category_id or product_id must be provided"
		) from e
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
