import fastapi
import uuid
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from exceptions.banner import BannerNotFoundError, EmptyEventsError
from exceptions.product import (
	InvalidSortError,
	InvalidSearchQueryError,
	ProductNotFoundError,
)
from exceptions.category import CategoryNotFoundError, CategoryHierarchyError
from schemas.banner import Banner, BannerEventsRequest
from schemas.catalog import (
	CatalogProductCard,
	CategoryRef,
	CategoryTreeNode,
	PaginatedCatalogProducts,
)
from schemas.category import CategoryInfoResponse, FacetsResponse, FilterResponse

from schemas.collection import Collection
from services import (
	banner_service,
	collection_service,
	product_service,
	category_service,
)
from core.db import get_db

router = fastapi.APIRouter(prefix="/api/v1/catalog")


class JsonFilterExtractor:
	def __init__(
		self,  # noqa
		request: Request,
		filter: Annotated[
			Optional[str],
			fastapi.Query(
				description="Фильтрация по параметрам",
				json_schema_extra={
					"type": "object",
					"properties": {
						"category_id": {
							"type": "string",
							"format": "uuid",
							"default": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
						},
						"price_min": {"type": "integer", "default": 0},
						"price_max": {"type": "integer", "default": 0},
						"seller_id": {
							"type": "string",
							"format": "uuid",
							"default": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
						},
						"attributes": {
							"type": "object",
							"properties": {
								"additionalProp1": {
									"type": "string",
									"default": "string",
								},
								"additionalProp2": {
									"type": "string",
									"default": "string",
								},
								"additionalProp3": {
									"type": "string",
									"default": "string",
								},
							},
							"default": {
								"additionalProp1": "string",
								"additionalProp2": "string",
								"additionalProp3": "string",
							},
						},
					},
				},
			),
		] = None,
	) -> None:
		self.params = product_service.parse_catalog_filters(
			query_params=request.query_params.multi_items(), filter_str=filter
		)


@router.get("/categories/tree", response_model=list[CategoryTreeNode])
async def get_categories_tree(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
) -> list[CategoryTreeNode]:
	"""Get categories tree

	Args:
	    db (Annotated[AsyncSession, fastapi.Depends]): Database session

	Returns:
	    list[CategoryTreeNode]: Categories tree
	"""
	try:
		return await category_service.get_categories_tree(db)
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/categories", response_model=list[CategoryRef])
async def get_categories_flat(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
) -> list[CategoryRef]:
	"""Get flat categories

	Args:
	    db (Annotated[AsyncSession, fastapi.Depends]): Database session

	Returns:
	    list[CategoryRef]: Flat categories
	"""
	try:
		return await category_service.get_categories_flat(db)
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/categories/{category_id}", response_model=CategoryInfoResponse)
async def get_category_info(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
	category_id: str,
	include_product_count: bool = False,
) -> CategoryInfoResponse:
	"""Get category info

	Args:
	    db (Annotated[AsyncSession, fastapi.Depends]): Database session
	    category_id (str): Category ID
	    include_product_count (bool, optional): Include product count

	Returns:
	    CategoryInfoResponse: Category info
	"""
	try:
		return await category_service.get_category_info(
			db, category_id, include_product_count
		)
	except ValueError as e:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "INVALID_REQUEST", "message": "id must be a valid UUID"},
		) from e
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/categories/{category_id}/filters", response_model=FilterResponse)
async def get_category_filters(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
	category_id: str,
) -> FilterResponse:
	"""Get category filters

	Args:
	    db (Annotated[AsyncSession, fastapi.Depends]): Database session
	    category_id (str): Category ID

	Returns:
	    FilterResponse: Category filters
	"""
	try:
		return await category_service.get_category_filters(db, category_id)
	except ValueError as e:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "INVALID_REQUEST", "message": "id must be a valid UUID"},
		) from e
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(e)},
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/facets", response_model=FacetsResponse)
async def get_facets(
	request: Request,
	category_id: uuid.UUID,
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
) -> FacetsResponse:
	try:
		facets_data = await product_service.get_catalog_facets_service(
			db, str(category_id), request.query_params.multi_items()
		)
		return facets_data
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404, detail={"code": "CATEGORY_NOT_FOUND", "message": str(e)}
		) from e
	except CategoryHierarchyError as e:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "CATEGORY_HIERARCHY_ERROR", "message": str(e)},
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e


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


@router.get(
	"/products/{product_id}/similar",
	response_model=list[CatalogProductCard],
)
async def get_similar_products_api(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
	product_id: uuid.UUID,
	limit: Annotated[int, fastapi.Query(ge=1, le=50)] = 10,
) -> list[CatalogProductCard]:
	try:
		return await product_service.get_similar_products(db, product_id, limit)
	except ProductNotFoundError as err:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(err)},
		) from err
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e


@router.get("/products", response_model=PaginatedCatalogProducts)
async def get_product_list_api(
	db: Annotated[AsyncSession, fastapi.Depends(get_db)],
	limit: int = 20,
	offset: int = 0,
	q: Optional[str] = None,
	sort: str = fastapi.Query(
		default="popularity",
		enum=["price_asc", "price_desc", "popularity", "new"],
	),
	filter_extractor: JsonFilterExtractor = fastapi.Depends(),  # noqa
) -> PaginatedCatalogProducts:
	try:
		filters_obj = filter_extractor.params
		return await product_service.get_products_list(
			db,
			limit,
			offset,
			filters_obj,
			sort,
			q,
		)
	except (InvalidSortError, InvalidSearchQueryError) as e:
		raise fastapi.HTTPException(
			status_code=400, detail={"code": "INVALID_REQUEST", "message": str(e)}
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e
