from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from database.models import Product


async def get_sku_by_id(db: AsyncSession, product_id: UUID) -> Product | None:
    """Check if a product exists in the database."""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    return result.scalar_one_or_none()
