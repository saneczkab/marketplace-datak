from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from crud import sku as sku_crud
from exceptions.sku import SkuNotFoundError
from exceptions.product import ProductNotFoundError

from crud import product as product_crud


async def create_sku(db: AsyncSession, data: dict):
    """Logic for creating a SKU. Validates product existence first."""
    product = await product_crud.get_sku_by_id(db, data["product_id"])
    if not product:
        raise ProductNotFoundError(f"Product with id {data['product_id']} not found")

    return await sku_crud.create(db, data)


async def get_sku(db: AsyncSession, sku_id: UUID):
    """Logic for retrieving a SKU. Validates existence."""
    sku = await sku_crud.get_sku_by_id(db, sku_id)
    if not sku:
        raise SkuNotFoundError(f"SKU with id {sku_id} not found")
    return sku


async def update_sku(db: AsyncSession, sku_id: UUID, data: dict):
    """Logic for updating a SKU."""
    sku = await sku_crud.update(db, sku_id, data)
    if not sku:
        raise SkuNotFoundError(f"SKU with id {sku_id} not found")
    return sku


async def get_skus_by_product(db: AsyncSession, product_id: UUID):
    """Retrieve all SKUs for a product."""
    return await sku_crud.get_by_product(db, product_id)
