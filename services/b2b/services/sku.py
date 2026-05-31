from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import images as images_crud
from crud import product as product_crud
from crud import sku as sku_crud
from database.models.catalog.base import Product, ProductStatusEnum
from database.models.catalog.variants import Sku
from exceptions.product import ProductNotFoundError, ProductNotOwnerError
from exceptions.sku import SkuForbiddenError, SkuNotFoundError, SkuValidationError
from schemas.sku import (
	CharacteristicSchema,
	ImageAttachRequest,
	ImageSchema,
	SkuCreate,
	SkuImageResponse,
	SkuResponse,
)


def _prepare_sku_data(data: SkuCreate) -> dict:
	payload = data.model_dump()
	payload["cost_price"] = (
		payload.get("cost_price") if payload.get("cost_price") is not None else 0
	)
	payload["article"] = payload.get("article") or ""
	return payload


async def build_sku_response(db: AsyncSession, sku: Sku) -> SkuResponse:
	images = await sku_crud.load_images_for_sku(db, sku.id)
	return SkuResponse(
		id=sku.id,
		product_id=sku.product_id,
		name=sku.name,
		price=sku.price,
		discount=sku.discount,
		cost_price=sku.cost_price or None,
		stock_quantity=sku.stock_quantity,
		active_quantity=sku.active_quantity,
		reserved_quantity=sku.reserved_quantity,
		article=sku.article or None,
		characteristics=[
			CharacteristicSchema.model_validate(c) for c in sku.characteristics
		],
		images=[ImageSchema.model_validate(img) for img in images],
		created_at=sku.created_at,
		updated_at=sku.updated_at,
	)


async def _get_owned_sku(
	db: AsyncSession, sku_id: UUID, seller_id: UUID
) -> tuple[Sku, Product]:
	sku = await sku_crud.get_sku_by_id(db, sku_id)
	if not sku:
		raise SkuNotFoundError(f"SKU with id {sku_id} not found")

	product = await product_crud.get_product_by_id_only(db, sku.product_id)
	if not product or product.seller_id != seller_id:
		raise ProductNotOwnerError("SKU does not belong to the authenticated seller")
	if product.status == ProductStatusEnum.HARD_BLOCKED:
		raise SkuForbiddenError("Cannot modify SKU of hard-blocked product")

	return sku, product


async def create_sku(db: AsyncSession, data: SkuCreate, seller_id: UUID) -> SkuResponse:
	product = await product_crud.get_product_by_id_only(db, data.product_id)
	if not product:
		raise ProductNotFoundError(f"Product with id {data.product_id} not found")
	if product.seller_id != seller_id:
		raise ProductNotOwnerError(
			"Product does not belong to the authenticated seller"
		)
	if product.status == ProductStatusEnum.HARD_BLOCKED:
		raise SkuForbiddenError("Cannot add SKU to hard-blocked product")
	if data.price <= 0:
		raise SkuValidationError("price must be a positive integer")

	sku = await sku_crud.create(db, _prepare_sku_data(data), product=product)
	return await build_sku_response(db, sku)


async def attach_sku_image(
	db: AsyncSession, sku_id: UUID, data: ImageAttachRequest, seller_id: UUID
) -> SkuImageResponse:
	if not data.url or not data.url.strip():
		raise SkuValidationError("url is required")

	sku, product = await _get_owned_sku(db, sku_id, seller_id)
	had_sku_image_before = await images_crud.product_has_sku_image(db, product.id)

	image = await images_crud.attach_sku_image(
		db, sku.id, data.url.strip(), data.ordering
	)
	await db.commit()
	await db.refresh(image)

	if product.status == ProductStatusEnum.CREATED and not had_sku_image_before:
		await sku_crud.transition_product_to_on_moderation(db, product)

	return SkuImageResponse.model_validate(image)


async def get_sku(db: AsyncSession, sku_id: UUID, seller_id: UUID) -> SkuResponse:
	await _get_owned_sku(db, sku_id, seller_id)
	sku = await sku_crud.get_sku_by_id(db, sku_id)
	return await build_sku_response(db, sku)


async def update_sku(
	db: AsyncSession, sku_id: UUID, data: dict, seller_id: UUID
) -> SkuResponse:
	await _get_owned_sku(db, sku_id, seller_id)

	updated = await sku_crud.update(db, sku_id, data)
	if not updated:
		raise SkuNotFoundError(f"SKU with id {sku_id} not found")
	return await build_sku_response(db, updated)


async def get_skus_by_product_id(
	db: AsyncSession, product_id: UUID, seller_id: UUID
) -> list[SkuResponse]:
	product = await product_crud.get_product_by_id(db, product_id, seller_id)
	if not product:
		raise ProductNotFoundError(f"Product with id {product_id} not found")

	skus = await sku_crud.get_by_product_id(db, product_id)
	return [await build_sku_response(db, sku) for sku in skus]
