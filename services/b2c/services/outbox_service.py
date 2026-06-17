from schemas.event import Event, EventTypeEnum, OrderFulfilledItem
import crud.outbox as outbox_crud
import order_service

from sqlalchemy.ext.asyncio import AsyncSession
import uuid


async def create_order_fulfilled_event(
	order_id: uuid.UUID, buyer_id: uuid.UUID, db: AsyncSession
) -> None:
	order_info = await order_service.get_order_by_id_for_buyer(
		db, order_id, buyer_id=buyer_id
	)
	event = Event(event_type=EventTypeEnum.ORDER_FULFILLED, order_id=order_id, items=[])

	for item in order_info.items:
		event.items.append(OrderFulfilledItem(item.sku_id, item.quantity))

	await outbox_crud.post_event(event, db)
