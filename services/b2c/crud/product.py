from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from database.models.catalog.base import Product

async def count_products_in_category(db: AsyncSession, category_id: uuid.UUID) -> int:
    result = await db.execute(
        select(Product).where(Product.category_id == category_id)
    )
    return result.scalars().count()