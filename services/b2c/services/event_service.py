from sqlalchemy.ext.asyncio import AsyncSession

import crud.event as event_crud
from database.models import B2BEvent as db_B2BEvent
from schemas.event import B2BEvent as schema_B2BEvent
from schemas.event import EventProductRef
from exceptions.event import EventDuplicatError
from services import product_service
from services import cart_service
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
			await handle_product_blocked(event.payload, db)


async def handle_product_blocked(payload: EventProductRef, db: AsyncSession) -> None:
	"""Steps of handling
	1. Mark product as "BLOCKED" - Done
	2. Add notification for each cart to notify user this product has been blocked
	3. Delete product from each cart
	"""

	await product_service.mark_product_blocked(payload, db)

	# No notifications yet

	skus = await product_crud.get_product_skus(db, payload.product_id)

	for sku in skus:
		gen = cart_crud.get_carts_with_product(sku.id, db)
		async for cart in gen:
			cart_service.remove_cart_item(db, user_id=cart.user_id, sku_id=sku.id)
