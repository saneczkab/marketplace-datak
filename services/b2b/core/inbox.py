"""
Обработка входящих сообщений из бд
"""

from core.db import get_db_context
from core.config import settings
import crud.inbox as inbox_crud

import logging
import asyncio

logger = logging.getLogger("Inbox handling")


async def process_events() -> None:
	"""
	Get all pending events and handle them by their event_type
	"""
	async with get_db_context() as db:
		events = await inbox_crud.get_all_pending_events(db)

	for event in events:
		logger.info(f"Handling event {event.idempotency_key} ({event.event_type})")
		try:
			# All logic here
			pass
		except Exception as e:  # noqa
			logger.error(f"Failed to handle event {event.idempotency_key}: {e}")
			inbox_crud.mark_event_failed(event, db)


async def run_inbox_messages_handling() -> None:
	while True:
		await process_events()
		await asyncio.sleep(settings.INBOX_MESSAGES_PROCESSING_DELAY)
