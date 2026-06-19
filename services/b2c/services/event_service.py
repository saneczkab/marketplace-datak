import logging
from sqlalchemy.ext.asyncio import AsyncSession

import crud.inbox as inbox_crud
import crud.product as product_crud
import crud.cart as cart_crud
from database.models import InboxEvent
from database.models.event.inbox import InboxEventStatusEnum
from schemas.event import Event as B2BEventSchema, EventPriceChanged, EventSkuStock
from schemas.event import EventProductRef
from exceptions.event import EventDuplicatError
from services import (
	notification_service,
	product_service,
	cart_service,
	sku_service,
	favorite_service,
)

logger = logging.getLogger("Event service")


async def handle_b2b_event(
	event: B2BEventSchema,
	db: AsyncSession,
) -> None:
	"""Saves event in db to be processed"""
	dbevent: InboxEvent = await inbox_crud.get_event_by_idempotency_key(
		event.idempotency_key, db
	)

	if dbevent:
		raise EventDuplicatError

	logger.info(f"Adding event {event.idempotency_key} - {event.event_type}")

	await inbox_crud.add_event(
		InboxEvent(
			idempotency_key=str(event.idempotency_key),
			event_type=event.event_type,
			routing_key="",
			occurred_at=event.occurred_at,
			payload=event.payload.model_dump(mode="json"),
			status=InboxEventStatusEnum.PENDING,
		),
		db,
	)


async def process_b2b_event(event: B2BEventSchema, db: AsyncSession) -> None:
	match event.event_type:
		case "PRODUCT_BLOCKED":
			await handle_product_blocked(event.payload, db, False)
		case "PRODUCT_HARD_BLOCKED":
			await handle_product_blocked(event.payload, db, True)
		case "PRODUCT_DELETED":
			await handle_product_deleted(event.payload, db)
		case "SKU_OUT_OF_STOCK":
			await handle_sku_out_of_stock(event.payload, db)
		case "SKU_BACK_IN_STOCK":
			await handle_sku_back_in_stock(event.payload, db)
		case "PRICE_CHANGED":
			await handle_price_changed(event.payload, db)


# =============== HANDLERS ===============


async def handle_product_blocked(
	payload: EventProductRef, db: AsyncSession, is_hard_blocked: bool
) -> None:
	"""Steps of handling
	1. Mark product as "BLOCKED" - Done
	2. Add notification for each cart to notify user this product has been blocked - If hard blocked it changes
	3. Delete product from each cart

	TODO: reason can be None, add handling of that case
	"""

	await product_service.mark_product_blocked(payload, is_hard_blocked, db)

	skus = await product_crud.get_product_skus(db, payload.product_id)

	for sku in skus:
		gen = cart_crud.get_carts_with_product(sku.id, db)
		async for cart in gen:
			await notification_service.notification_product_blocked(
				cart.user_id, sku.id, is_hard_blocked
			)
			await cart_service.remove_cart_item(
				db, user_id=cart.user_id, session_id=None, sku_id=sku.id
			)
	await favorite_service.mark_product_unavailable(db, payload.product_id)


async def handle_sku_out_of_stock(payload: EventSkuStock, db: AsyncSession) -> None:
	"""
	Steps
	1. Update stock in database
	2. Add notification for each cart
	3. Delete from each cart
	"""
	await sku_service.update_sku_stock(db, payload.sku_id, payload.available_quantity)

	gen = cart_crud.get_carts_with_product(payload.sku_id, db)
	async for cart in gen:
		await notification_service.notification_sku_out_of_stock(
			cart, payload.sku_id, db
		)
		await cart_service.remove_cart_item(
			db, user_id=cart.user_id, sku_id=payload.sku_id
		)


async def handle_sku_back_in_stock(payload: EventSkuStock, db: AsyncSession) -> None:
	await sku_service.update_sku_stock(db, payload.sku_id, payload.available_quantity)
	await notification_service.notification_sku_back_in_stock(payload.sku_id)


async def handle_price_changed(payload: EventPriceChanged, db: AsyncSession) -> None:
	await sku_service.update_sku_price(db, payload.sku_id, payload.new_price)

	await notification_service.notification_sku_price_change(
		payload.sku_id, payload.old_price, payload.new_price
	)


async def handle_product_deleted(payload: EventProductRef, db: AsyncSession) -> None:

	await product_service.delete_product(payload.product_id, db)
	await notification_service.notification_product_deleted()
