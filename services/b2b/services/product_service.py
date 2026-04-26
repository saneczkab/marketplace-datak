from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog.base import ProductStatusEnum
from exceptions.product import ProductNotFoundError
from uuid import UUID
from schemas.product import ProductCreate, ProductUpdate
from fastapi import HTTPException, status

SELLER_TRANSITIONS = {
	ProductStatusEnum.CREATED: [
		ProductStatusEnum.ON_MODERATION,
		ProductStatusEnum.DELETED,
	],
	ProductStatusEnum.ON_MODERATION: [
		ProductStatusEnum.CREATED,
		ProductStatusEnum.DELETED,
	],
	ProductStatusEnum.MODERATED: [ProductStatusEnum.CREATED, ProductStatusEnum.DELETED],
	ProductStatusEnum.BLOCKED: [ProductStatusEnum.DELETED],
	ProductStatusEnum.DELETED: [ProductStatusEnum.CREATED],
}

ADMIN_TRANSITIONS = {
	ProductStatusEnum.ON_MODERATION: [
		ProductStatusEnum.MODERATED,
		ProductStatusEnum.CREATED,
		ProductStatusEnum.BLOCKED,
	],
	ProductStatusEnum.MODERATED: [ProductStatusEnum.BLOCKED],
	ProductStatusEnum.CREATED: [ProductStatusEnum.BLOCKED],
}


async def create_new_product(
	db: AsyncSession, product_in: ProductCreate, seller_id: UUID
):
	return await product_crud.create_product(db, product_in, seller_id)


async def get_product_for_seller(db: AsyncSession, product_id: UUID, seller_id: UUID):
	product = await product_crud.get_product_by_id(db, product_id, seller_id)
	if not product:
		raise ProductNotFoundError("Product not found or access denied")
	return product


async def get_all_seller_products(db: AsyncSession, seller_id: UUID):
	return await product_crud.get_seller_products(db, seller_id)


async def patch_existing_product(
	db: AsyncSession, product_id: UUID, seller_id: UUID, product_in: ProductUpdate
):
	db_product = await get_product_for_seller(db, product_id, seller_id)

	update_data = product_in.model_dump(exclude_unset=True)

	updated_product = await product_crud.update_product(db, db_product, update_data)

	return updated_product


from crud import product as product_crud


async def remove_product(db: AsyncSession, product_id: UUID, seller_id: UUID):
	product = await get_product_for_seller(db, product_id, seller_id)

	await product_crud.soft_delete_product(db, product)

	return {"detail": "Product deleted successfully"}


async def change_product_status(
	db: AsyncSession,
	product_id: UUID,
	seller_id: UUID,
	new_status: ProductStatusEnum,
	is_admin: bool = False,
):
	product = await get_product_for_seller(db, product_id, seller_id)
	old_status = product.status

	transitions = ADMIN_TRANSITIONS if is_admin else SELLER_TRANSITIONS

	if new_status not in transitions.get(old_status, []):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Нельзя перевести товар из {old_status} в {new_status}",
		)

	product.status = new_status
	await db.commit()
	await db.refresh(product)

	return product
