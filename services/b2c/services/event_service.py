from sqlalchemy.ext.asyncio import AsyncSession

import crud.event as event_crud
from database.models import B2BEvent as db_B2BEvent
from schemas.event import B2BEvent as schema_B2BEvent, EventSkuStock
from schemas.event import EventProductRef
from exceptions.event import EventDuplicatError
from services import notification_service, product_service, cart_service, sku_service
import crud.product as product_crud
import crud.cart as cart_crud


async def handle_b2b_event(event: schema_B2BEvent, db: AsyncSession) -> None:
	dbevent: db_B2BEvent = await event_crud.get_event_by_idempotency_key(
		event.idempotency_key, db
	)

	if dbevent:
		raise EventDuplicatError

	await event_crud.add_event(
		db_B2BEvent(idempotency_key=event.idempotency_key, event_type=event.event_type),
		db,
	)

	match event.event_type:
		case "PRODUCT_BLOCKED":
			await handle_product_blocked(event.payload, db, False)
		case "PRODUCT_HARD_BLOCKED":
			await handle_product_blocked(event.payload, db, True)
		case "SKU_OUT_OF_STOCK":
			await handle_sku_out_of_stock(event.payload, db)


async def handle_product_blocked(
	payload: EventProductRef, db: AsyncSession, is_hard_blocked: bool
) -> None:
	"""Steps of handling
	1. Mark product as "BLOCKED" - Done
	2. Add notification for each cart to notify user this product has been blocked - If hard blocked it changes
	3. Delete product from each cart
	"""

	await product_service.mark_product_blocked(payload, is_hard_blocked, db)

	skus = await product_crud.get_product_skus(db, payload.product_id)

	for sku in skus:
		gen = cart_crud.get_carts_with_product(sku.id, db)
		async for cart in gen:
			await notification_service.notification_product_blocked(
				cart.user_id, sku.id, is_hard_blocked
			)
			await cart_service.remove_cart_item(db, user_id=cart.user_id, sku_id=sku.id)


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


async def sku_stock_change(payload: EventSkuStock, db: AsyncSession) -> None:
	pass
