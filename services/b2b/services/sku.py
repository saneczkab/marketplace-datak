from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from crud import sku as sku_crud

async def create_sku(db: AsyncSession, data: dict):
    return await sku_crud.create(db, data)

async def update_sku(db: AsyncSession, sku_id: UUID, data: dict):
    return await sku_crud.update(db, sku_id, data)

async def get_sku(db: AsyncSession, sku_id: UUID):
    return await sku_crud.get_by_id(db, sku_id)

async def get_skus_by_product(db: AsyncSession, product_id: UUID):
    return await sku_crud.get_by_product(db, product_id)