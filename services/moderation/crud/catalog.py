from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.catalog.base import Category, Product, ProductStatusEnum
from database.models.catalog.variants import Characteristic, Image, Sku
from schemas.catalog_event import (
	CategoryPayload,
	ProductUpdatePayload,
	SkuPayload,
	SkuUpdatePayload,
)
from schemas.product_snapshot import (
	ProductSnapshot,
	ProductSnapshotCategory,
	ProductSnapshotCharacteristic,
	ProductSnapshotImage,
	ProductSnapshotSku,
)


async def get_product_full(db: AsyncSession, product_id: UUID) -> Product | None:
	result = await db.execute(
		select(Product)
		.options(
			selectinload(Product.category),
			selectinload(Product.skus).selectinload(Sku.images),
			selectinload(Product.skus).selectinload(Sku.characteristics),
			selectinload(Product.images),
			selectinload(Product.characteristics),
		)
		.where(Product.id == product_id)
	)
	return result.scalar_one_or_none()


async def _upsert_category(db: AsyncSession, payload: CategoryPayload) -> Category:
	category = await db.get(Category, payload.id)
	if category is None:
		category = Category(id=payload.id, name=payload.name)
		db.add(category)
	else:
		category.name = payload.name
	await db.flush()
	return category


def _build_sku_entity(product_id: UUID, payload: SkuPayload | SkuUpdatePayload) -> Sku:
	sku = Sku(
		id=payload.id,
		product_id=product_id,
		name=payload.name,
		price=payload.price,
		discount=payload.discount,
		active_quantity=payload.active_quantity,
		article=payload.article,
	)
	sku.images = [
		Image(
			id=image.id,
			product_id=None,
			sku_id=payload.id,
			url=image.url,
			ordering=image.ordering,
		)
		for image in payload.images
	]
	sku.characteristics = [
		Characteristic(
			id=item.id,
			product_id=None,
			sku_id=payload.id,
			name=item.name,
			value=item.value,
		)
		for item in payload.characteristics
	]
	return sku


async def upsert_product(db: AsyncSession, payload: ProductUpdatePayload) -> Product:
	category_data = payload.category or CategoryPayload(
		id=payload.category_id, name="Unknown"
	)
	await _upsert_category(db, category_data)

	product = await get_product_full(db, payload.id)
	if product is None:
		product = Product(
			id=payload.id,
			seller_id=payload.seller_id,
			category_id=payload.category_id,
			title=payload.title,
			slug=payload.slug,
			description=payload.description,
			status=ProductStatusEnum(payload.status),
			deleted=payload.deleted,
		)
		db.add(product)
	else:
		product.seller_id = payload.seller_id
		product.category_id = payload.category_id
		product.title = payload.title
		product.slug = payload.slug
		product.description = payload.description
		product.status = ProductStatusEnum(payload.status)
		product.deleted = payload.deleted

	product.images = [
		Image(
			id=image.id,
			product_id=payload.id,
			sku_id=None,
			url=image.url,
			ordering=image.ordering,
		)
		for image in payload.images
	]
	product.characteristics = [
		Characteristic(
			id=item.id,
			product_id=payload.id,
			sku_id=None,
			name=item.name,
			value=item.value,
		)
		for item in payload.characteristics
	]
	product.skus = [_build_sku_entity(payload.id, sku) for sku in payload.skus]
	await db.flush()
	return product


async def upsert_sku(db: AsyncSession, payload: SkuUpdatePayload) -> Sku:
	product = await db.get(Product, payload.product_id)
	if product is None:
		raise ValueError(f"Product {payload.product_id} not found in catalog replica")

	existing = await db.get(Sku, payload.id)
	if existing is not None:
		await db.delete(existing)
		await db.flush()

	sku = _build_sku_entity(payload.product_id, payload)
	db.add(sku)
	await db.flush()
	return sku


def build_product_snapshot_from_entity(product: Product) -> ProductSnapshot:
	sku_images_by_sku = {
		sku.id: sorted(sku.images, key=lambda image: image.ordering)
		for sku in product.skus
	}
	first_sku_image_url = None
	if product.skus and sku_images_by_sku.get(product.skus[0].id):
		first_sku_image_url = sku_images_by_sku[product.skus[0].id][0].url

	return ProductSnapshot(
		id=product.id,
		seller_id=product.seller_id,
		category_id=product.category_id,
		title=product.title,
		slug=product.slug,
		description=product.description or "",
		status=product.status.value,
		deleted=product.deleted,
		blocked=False,
		category=ProductSnapshotCategory(
			id=product.category.id,
			name=product.category.name,
		),
		images=[
			ProductSnapshotImage(
				id=image.id,
				url=image.url,
				ordering=image.ordering,
			)
			for image in sorted(product.images, key=lambda item: item.ordering)
		],
		characteristics=[
			ProductSnapshotCharacteristic(
				id=item.id,
				name=item.name,
				value=item.value,
			)
			for item in product.characteristics
		],
		skus=[
			ProductSnapshotSku(
				id=sku.id,
				product_id=sku.product_id,
				name=sku.name,
				price=sku.price,
				discount=sku.discount,
				active_quantity=sku.active_quantity,
				article=sku.article,
				image=(
					sku_images_by_sku[sku.id][0].url
					if sku_images_by_sku.get(sku.id)
					else first_sku_image_url
				),
				images=[
					ProductSnapshotImage(
						id=image.id,
						url=image.url,
						ordering=image.ordering,
					)
					for image in sku_images_by_sku.get(sku.id, [])
				],
				characteristics=[
					ProductSnapshotCharacteristic(
						id=item.id,
						name=item.name,
						value=item.value,
					)
					for item in sku.characteristics
				],
			)
			for sku in product.skus
		],
		blocking_reason=None,
		field_reports=[],
	)


async def build_product_snapshot(
	db: AsyncSession, product_id: UUID
) -> ProductSnapshot | None:
	product = await get_product_full(db, product_id)
	if product is None:
		return None
	return build_product_snapshot_from_entity(product)
