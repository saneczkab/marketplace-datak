from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import product as product_crud
from crud import session as session_crud
from database.models import Session
from database.models.catalog.base import Product, ProductStatusEnum
from exceptions.product import (
	ProductForbiddenError,
	ProductNotFoundError,
	ProductNotOwnerError,
)
from schemas.product import ProductCreate, ProductResponse, ProductUpdate


def build_product_response(product: Product) -> ProductResponse:
	return ProductResponse(
		id=product.id,
		seller_id=product.seller_id,
		category_id=product.category_id,
		title=product.title,
		slug=product.slug,
		description=product.description,
		status=product.status,
		deleted=product.deleted,
		blocking_reason_id=product.blocked_reason_id,
		moderator_comment=product.moderator_comment,
		images=[],
		characteristics=[],
		skus=[],
		created_at=product.created_at,
		updated_at=product.updated_at,
	)


async def _get_owned_product(
	db: AsyncSession, product_id: UUID, seller_id: UUID
) -> Product:
	product = await product_crud.get_product_by_id_only(db, product_id)
	if product is None:
		raise ProductNotFoundError()
	if product.seller_id != seller_id:
		raise ProductNotOwnerError()
	if product.status == ProductStatusEnum.HARD_BLOCKED:
		raise ProductForbiddenError("Can't edit hard-blocked product")
	return product


async def create_new_product(
	db: AsyncSession, product_in: ProductCreate, seller_token: UUID
) -> ProductResponse:
	session: Session = await session_crud.get_session_by_access_token(seller_token, db)

	product = Product(
		seller_id=session.user_id,
		category_id=product_in.category_id,
		title=product_in.title,
		slug=product_in.slug,
		description=product_in.description,
		status=ProductStatusEnum.CREATED,
		deleted=False,
		moderator_comment="",
	)

	product = await product_crud.add_product(product, db)
	return build_product_response(product)


async def get_product_for_seller(
	db: AsyncSession, product_id: UUID, seller_id: UUID
) -> Product:
	product = await product_crud.get_product_by_id(db, product_id, seller_id)
	if not product:
		raise ProductNotFoundError("Product not found or access denied")
	return product


async def get_all_seller_products(db: AsyncSession, seller_id: UUID) -> list[Product]:
	return await product_crud.get_seller_products(db, seller_id)


async def patch_existing_product(
	db: AsyncSession, product_id: UUID, seller_id: UUID, product_in: ProductUpdate
) -> ProductResponse:
	product = await _get_owned_product(db, product_id, seller_id)
	submit_for_remoderation = product.status in [
		ProductStatusEnum.BLOCKED,
		ProductStatusEnum.MODERATED,
	]

	update_data = product_in.model_dump(exclude_unset=True)
	updated_product = await product_crud.update_product(
		db,
		product,
		update_data,
		should_remoderate=submit_for_remoderation,
	)
	return build_product_response(updated_product)


async def remove_product(
	db: AsyncSession, product_id: UUID, seller_id: UUID
) -> dict[str, str]:
	product = await get_product_for_seller(db, product_id, seller_id)

	await product_crud.soft_delete_product(db, product)

	return {"detail": "Product deleted successfully"}
