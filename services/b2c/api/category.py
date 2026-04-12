import fastapi

from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.category import (
	CategoryInfoResponse,
	CategoryTreeResponse,
	FilterResponse,
	FacetResonse,
)
from exceptions.category import CategoryNotFoundError
import services.category_service as category_service

from core import db

router = fastapi.APIRouter(prefix="/api/v1/categories")


@router.get("/{id}")
async def get_category_info(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	id: str,
	include_product_count: bool = False,
	lang: str = "ru",  # noqa
) -> CategoryInfoResponse:
	"""Category info endpoint

	Args:
		db (AsyncSession): database session
		id (str): category id
		include_product_count (bool, optional): whether to include product count. Defaults to False.
		lang (str, optional): language code. Defaults to "ru". Actually does nothing

	Raises:
		fastapi.HTTPException(404): Category not found
		fastapi.HTTPException(400): Invalid UUID format
		fastapi.HTTPException(503): Other errors

	Returns:
		CategoryInfoResponse: The category information
	"""
	try:
		return await category_service.get_category_info(db, id, include_product_count)
	except ValueError as e:
		raise fastapi.HTTPException(
			status_code=400, detail="id must be a valid UUID"
		) from e
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("")
async def get_categories_tree(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> CategoryTreeResponse:
	"""Builds categories tree

	Args:
		db (AsyncSession): database session

	Raises:
		fastapi.HTTPException(404): Root category not found
		fastapi.HTTPException(503): Other errors

	Returns:
		CategoryTreeResponse: The categories tree
	"""
	try:
		return await category_service.get_categories_tree(db)
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(
			status_code=404, detail="Root category not found. Check database"
		) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/{id}/filters")
async def get_category_filters(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	id: str,
) -> FilterResponse:
	"""Lists filters for category

	Args:
		db (AsyncSession): database session
		id (str): category id

	Raises:
		fastapi.HTTPException(400): Invalid UUID format
		fastapi.HTTPException(404): Category not found
		fastapi.HTTPException(503): Other errors

	Returns:
		FilterResponse: The list of filters for the category
	"""
	try:
		return await category_service.get_category_filters(db, id)
	except ValueError as e:
		raise fastapi.HTTPException(
			status_code=400, detail="id must be a valid UUID"
		) from e
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/{id}/facets")
async def get_category_facets(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	id: str,
	filters: str | None = None,
) -> FacetResonse:
	"""Lists facets for category with applied filters

	Args:
		db (AsyncSession): database session
		id (str): category id
		filters (str | None, optional): applied filters. Defaults to None.

	Raises:
		fastapi.HTTPException(400): Invalid UUID format
		fastapi.HTTPException(404): Category not found
		fastapi.HTTPException(503): Other errors

	Returns:
		FacetResonse: The list of facets for the category with applied filters
	"""
	try:
		return await category_service.get_category_facets(db, id, filters)
	except ValueError as e:
		raise fastapi.HTTPException(
			status_code=400, detail="id must be a valid UUID"
		) from e
	except CategoryNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
