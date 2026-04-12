from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Result, select
import uuid
from database.models.catalog.base import Category, FilterValues
from schemas.category import FilterResponse
from exceptions.category import CategoryNotFoundError


async def get_category_by_id(
	db: AsyncSession, category_id: uuid.UUID
) -> Category | None:

	result: Result[Tuple[Category]] = await db.execute(
		select(Category).where(Category.id == category_id)
	)
	return result.scalars().first()


async def get_categories_by_parent_id(
	db: AsyncSession, parent_id: uuid.UUID | None
) -> list[Category]:

	result: Result[Tuple[Category]] = await db.execute(
		select(Category).where(Category.parent_id == parent_id)
	)
	return result.scalars().all()


async def get_category_filters(
	db: AsyncSession, category_id: uuid.UUID
) -> FilterResponse:
	exists = await db.execute(select(Category.id).where(Category.id == category_id))
	if not exists.scalars().first():
		raise CategoryNotFoundError(f"Category with id {category_id} not found")

	filters = await db.execute(
		select(FilterResponse).where(FilterResponse.category_id == category_id)
	)
	return filters.scalars().all()


async def get_filter_values(db: AsyncSession, filter_id: uuid.UUID) -> list[str]:
	result = await db.execute(
		select(FilterValues.value).where(FilterValues.filter_id == filter_id)
	)
	return result.scalars().all()
