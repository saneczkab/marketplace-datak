import uuid
from sqlalchemy.ext.asyncio import AsyncSession

import crud.subscription as sub_crud
from schemas.subscription import SubscribeRequest, SubscriptionResponse
from schemas.collection import ProductSchema, Category, Characteristic, SKU
from exceptions.subscription import (
	SubscriptionNotFoundError,
	SubscriptionAlreadyExistsError,
	InvalidSubscriptionTypeError,
)
from exceptions.product import ProductNotFoundError


async def subscribe_to_product(
	db: AsyncSession,
	user_id: uuid.UUID,
	product_id: uuid.UUID,
	request: SubscribeRequest,
) -> SubscriptionResponse:
	valid_types = {"IN_STOCK", "PRICE_DOWN"}
	invalid_types = set(request.notify_on) - valid_types
	if invalid_types:
		raise InvalidSubscriptionTypeError("Допустимые типы IN_STOCK, PRICE_DOWN")

	notify_in_stock = "IN_STOCK" in request.notify_on
	notify_price_down = "PRICE_DOWN" in request.notify_on

	product_db = await sub_crud.get_product_for_subscription(db, product_id)
	if not product_db:
		raise ProductNotFoundError("Товар не найден")

	existing_sub = await sub_crud.get_subscription(db, user_id, product_id)
	if existing_sub:
		raise SubscriptionAlreadyExistsError("Вы уже подписаны на этот товар")

	subscription = await sub_crud.create_subscription(
		db=db,
		user_id=user_id,
		product_id=product_id,
		notify_in_stock=notify_in_stock,
		notify_price_down=notify_price_down,
	)

	saved_notify_on = []
	if subscription.notify_in_stock:
		saved_notify_on.append("IN_STOCK")
	if subscription.notify_price_down:
		saved_notify_on.append("PRICE_DOWN")

	if product_db.category:
		category_schema = Category(
			id=product_db.category.id, name=product_db.category.name
		)
	else:
		category_schema = Category(id=uuid.uuid4(), name="Без категории")

	skus_schema = []
	for sku in product_db.skus:
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

	product_schema = ProductSchema(
		id=product_db.id,
		title=product_db.title,
		description=product_db.description or "",
		status=product_db.status.name
		if hasattr(product_db.status, "name")
		else str(product_db.status),
		category=category_schema,
		images=[],
		characteristics=[],
		skus=skus_schema,
	)

	return SubscriptionResponse(
		id=subscription.id,
		product=product_schema,
		notify_on=saved_notify_on,
		created_at=subscription.created_at,
	)


async def unsubscribe_from_product(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> None:
	existing_sub = await sub_crud.get_subscription(db, user_id, product_id)
	if not existing_sub:
		raise SubscriptionNotFoundError("Вы не подписаны на этот товар")

	await sub_crud.delete_subscription(db, existing_sub)
