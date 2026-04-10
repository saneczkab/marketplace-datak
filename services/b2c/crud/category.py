from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Result, select
import uuid
from database.models.catalog.base import Category


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
