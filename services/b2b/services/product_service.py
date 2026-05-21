from sqlalchemy.ext.asyncio import AsyncSession
from crud import product as product_crud
from database.models.catalog.base import Product
from exceptions.product import ProductNotFoundError
from uuid import UUID
from schemas.product import ProductCreate, ProductUpdate, ProductResponse


async def create_new_product(
	db: AsyncSession, product_in: ProductCreate, seller_id: UUID
) -> ProductResponse:
	product: Product = await product_crud.create_product(db, product_in, seller_id)
	response = ProductResponse(
		id=product.id,
		seller_id=seller_id,
		category_id=product.category_id,
		title=product.title,
		slug=product.slug,
		description=product.description,
		status=product.status,
		deleted=product.deleted,
		blocking_reason_id=product.blocked_reason_id,
		moderator_comment=product.moderator_comment,
		images=[],  # TODO Add images,
		characteristics=[],  # TODO Add characteristics
		skus=[],  # TODO Add skus
		created_at=product.created_at,
		updated_at=product.updated_at,
	)

	return response


async def get_product_for_seller(
	db: AsyncSession, product_id: UUID, seller_id: UUID
) -> Product | None:
	product = await product_crud.get_product_by_id(db, product_id, seller_id)
	if not product:
		raise ProductNotFoundError("Product not found or access denied")
	return product


async def get_all_seller_products(db: AsyncSession, seller_id: UUID) -> list[Product]:
	return await product_crud.get_seller_products(db, seller_id)


async def patch_existing_product(
	db: AsyncSession, product_id: UUID, seller_id: UUID, product_in: ProductUpdate
) -> Product | None:
	db_product = await get_product_for_seller(db, product_id, seller_id)

	update_data = product_in.model_dump(exclude_unset=True)

	updated_product = await product_crud.update_product(db, db_product, update_data)

	return updated_product


async def remove_product(
	db: AsyncSession, product_id: UUID, seller_id: UUID
) -> dict[str, str]:
	product = await get_product_for_seller(db, product_id, seller_id)

	await product_crud.soft_delete_product(db, product)

	return {"detail": "Product deleted successfully"}
