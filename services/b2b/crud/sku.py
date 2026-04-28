from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from database.models.catalog.variants import Sku

async def create(db: AsyncSession, data: dict) -> Sku:
    chars_data = data.pop("characteristics", [])
    images_data = data.pop("images", [])
    
    sku = Sku(**data)
    db.add(sku)
    await db.commit()
    await db.refresh(sku)
    return sku

async def get_by_id(db: AsyncSession, sku_id: UUID) -> Sku | None:
    result = await db.execute(select(Sku).filter(Sku.id == sku_id))
    return result.scalar_one_or_none()

async def get_by_product(db: AsyncSession, product_id: UUID) -> list[Sku]:
    result = await db.execute(select(Sku).filter(Sku.product_id == product_id))
    return list(result.scalars().all())

async def update(db: AsyncSession, sku_id: UUID, data: dict) -> Sku | None:
    sku = await get_by_id(db, sku_id)
    if not sku:
        return None
    
    for key, value in data.items():
        setattr(sku, key, value)
    
    await db.commit()
    await db.refresh(sku)
    return sku