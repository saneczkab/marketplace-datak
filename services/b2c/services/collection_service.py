import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

import crud.collection as collection_crud
from schemas.collection import (
	CollectionsResponse,
	CollectionMetadata,
	CollectionBase,
	CollectionProductsResponse,
	ProductSchema,
	Category,
	Image,
	Characteristic,
	SKU,
)


async def get_collections_list(
	db: AsyncSession, limit: int, offset: int
) -> CollectionsResponse:
	collections_db = await collection_crud.get_active_collections(db, limit, offset)
	total_count = await collection_crud.count_active_collections(db)

	collections = [
		CollectionBase(
			id=col.id,
			title=col.title,
			description=col.description,
			cover_image_url=col.cover_image_url,
			target_url=col.target_url,
			priority=col.priority,
			start_date=col.start_date,
		)
		for col in collections_db
	]

	return CollectionsResponse(
		metadata=CollectionMetadata(
			total_count=total_count, limit=limit, offset=offset
		),
		collections=collections,
	)


async def get_collection_products(
	db: AsyncSession, collection_id: uuid.UUID, limit: int, offset: int
) -> CollectionProductsResponse:
	collection = await collection_crud.get_collection_by_id(db, collection_id)
	if not collection:
		raise HTTPException(status_code=404, detail="Подборка не найдена")

	all_product_ids = await collection_crud.get_collection_product_ids(
		db, collection_id
	)

	paginated_ids = list(all_product_ids)[offset : offset + limit]
	products_db = await collection_crud.get_products_by_ids(db, paginated_ids, limit, 0)

	found_product_ids = {p.id for p in products_db}
	unavailable_ids = [pid for pid in paginated_ids if pid not in found_product_ids]

	items = []
	for p in products_db:
		category_schema = (
			Category(id=p.category.id, name=p.category.name)
			if p.category
			else Category(id=uuid.uuid4(), name="Без категории")
		)

		images_schema = [Image(url=img.url, ordering=img.ordering) for img in p.images]
		chars_schema = [
			Characteristic(name=ch.name, value=ch.value) for ch in p.characteristics
		]

		skus_schema = []
		for sku in p.skus:
			sku_chars = [
				Characteristic(name=c.name, value=c.value) for c in sku.characteristics
			]
			skus_schema.append(
				SKU(
					id=sku.id,
					name=sku.name,
					price=sku.price,
					active_quantity=sku.active_quantity,
					characteristics=sku_chars,
				)
			)

		items.append(
			ProductSchema(
				id=p.id,
				title=p.title,
				description=p.description or "",
				status=p.status.name if hasattr(p.status, "name") else str(p.status),
				category=category_schema,
				images=images_schema,
				characteristics=chars_schema,
				skus=skus_schema,
			)
		)

	return CollectionProductsResponse(
		collection_title=collection.title,
		total_products=len(all_product_ids),
		items=items,
		unavailable_ids=unavailable_ids,
	)
