import asyncio
import logging

from crud import outbox as outbox_crud
from core.config import settings
from core.db import SessionLocal
from database.models.outbox import OutboxEvent, OutboxEventStatus
from messaging.publisher import publish_outbox_payload

logger = logging.getLogger(__name__)


async def process_pending_batch() -> int:
	processed = 0
	async with SessionLocal() as db:
		events = await outbox_crud.fetch_pending_events(db)

	for event in events:
		async with SessionLocal() as db:
			db_event = await db.get(OutboxEvent, event.id)
			if db_event is None or db_event.status != OutboxEventStatus.PENDING:
				continue
			try:
				await publish_outbox_payload(
					routing_key=db_event.routing_key,
					payload=db_event.payload,
				)
				await outbox_crud.mark_event_sent(db, db_event)
				processed += 1
			except Exception:
				logger.exception(
					"Failed to publish outbox event %s", db_event.idempotency_key
				)
				await db.rollback()
	return processed


async def run_forever() -> None:
	logger.info("Outbox worker started")
	while True:
		try:
			processed = await process_pending_batch()
			if processed:
				logger.info("Published %s outbox event(s)", processed)
		except Exception:
			logger.exception("Outbox worker iteration failed")
		await asyncio.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)
