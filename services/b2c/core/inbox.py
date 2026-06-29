"""
Обработка входящих сообщений в бд, вызов соответствующих методов
"""

from schemas.event import Event, EventOrderDelivered, dict_to_payload
from core.db import get_db_context
from core.config import settings
from crud import inbox as inbox_crud
import services.event_service as event_service

import asyncio
import logging

logger = logging.getLogger(__name__)


async def process_events() -> None:
	"""
	Gets pending events and handles them based on `event_type`\n
	"""
	async with get_db_context() as db:
		events = await inbox_crud.get_all_pending_events(db)

	for event in events:
		logger.info(f"Handling event {event.id} ({event.event_type})")
		try:
			match event.event_type:
				case (
					"PRODUCT_BLOCKED"
					| "PRODUCT_HARD_BLOCKED"
					| "PRODUCT_DELETED"
					| "SKU_OUT_OF_STOCK"
					| "PRICE_CHANGED"
					| "SKU_BACK_IN_STOCK"
				):
					b2bevent = Event(
						event_type=event.event_type,
						idempotency_key=event.idempotency_key,
						occurred_at=event.occurred_at,
						payload=dict_to_payload(event.event_type, event.payload),
					)
					async with get_db_context() as db:
						await event_service.process_b2b_event(b2bevent, db)

				case "ORDER_DELIVERED":
					order_event = Event(
						event_type=event.event_type,
						idempotency_key=event.idempotency_key,
						occurred_at=event.occurred_at,
						payload=EventOrderDelivered(
							order_id=event.payload["order_id"],
							buyer_id=event.payload["buyer_id"],
						),
					)

					async with get_db_context() as db:
						await event_service.process_order_event(order_event, db)

			async with get_db_context() as db:
				logger.info(f"Success handling event {event.id}")
				await inbox_crud.mark_event_proccessed(event.id, db)

		except Exception as e:  # noqa
			logger.error(
				f"Failed to proccess event {event.id} ({event.event_type}): {e}"
			)
			await inbox_crud.mark_event_failed(event.id, db)


async def run_inbox_messages_handling() -> None:
	while True:
		await process_events()
		await asyncio.sleep(settings.INBOX_MESSAGES_PROCESSING_DELAY)
