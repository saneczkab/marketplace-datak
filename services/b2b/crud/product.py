from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models.catalog.base import Product
from schemas.product import ProductCreate
from uuid import UUID

async def create_product(db: AsyncSession, obj_in: ProductCreate, seller_id: UUID) -> Product:
    db_obj = Product(
        **obj_in.model_dump(),
        seller_id=seller_id,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_seller_products(db: AsyncSession, seller_id: UUID) -> list[Product]:
    result = await db.execute(
        select(Product).where(Product.seller_id == seller_id)
    )
    return list(result.scalars().all())

async def get_product_by_id(db: AsyncSession, product_id: UUID, seller_id: UUID) -> Product | None:
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.seller_id == seller_id)
    )
    return result.scalar_one_or_none()