from sqlalchemy.ext.asyncio import AsyncSession
from crud import product as product_crud
from exceptions.product import ProductNotFoundError
from uuid import UUID
from schemas.product import ProductCreate, ProductUpdate


async def create_new_product(db: AsyncSession, product_in: ProductCreate, seller_id: UUID):
    return await product_crud.create_product(db, product_in, seller_id)

async def get_product_for_seller(db: AsyncSession, product_id: UUID, seller_id: UUID):
    product = await product_crud.get_product_by_id(db, product_id, seller_id)
    if not product:
        raise ProductNotFoundError("Product not found or access denied")
    return product

async def get_all_seller_products(db: AsyncSession, seller_id: UUID):
    return await product_crud.get_seller_products(db, seller_id)

async def patch_existing_product(db: AsyncSession, product_id: UUID, seller_id: UUID, product_in: ProductUpdate):
    db_product = await get_product_for_seller(db, product_id, seller_id)

    update_data = product_in.model_dump(exclude_unset=True)

    updated_product = await product_crud.update_product(db, db_product, update_data)

    return updated_product


from uuid import UUID
from crud import product as product_crud


async def remove_product(db: AsyncSession, product_id: UUID, seller_id: UUID):
    product = await get_product_for_seller(db, product_id, seller_id)

    await product_crud.soft_delete_product(db, product)

    return {"detail": "Product deleted successfully"}