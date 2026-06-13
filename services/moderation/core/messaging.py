import asyncio
import json
import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message

from core.config import settings
from core.db import SessionLocal
from crud import outbox as outbox_crud
from crud import processed_catalog_event as processed_catalog_event_crud
from exceptions.catalog import CatalogEventValidationError
from services import catalog_sync_service

CATALOG_EVENTS_QUEUE = "moderation.catalog.events"
CATALOG_EVENTS_ROUTING_KEY = "catalog.events"


def _rabbitmq_url() -> str:
	return (
		f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
		f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
	)


async def publish_message(routing_key: str, payload: dict) -> None:
	body = json.dumps(payload).encode("utf-8")
	connection = await aio_pika.connect_robust(_rabbitmq_url())
	async with connection:
		channel = await connection.channel()
		exchange = await channel.declare_exchange(
			settings.RABBITMQ_EXCHANGE,
			ExchangeType.TOPIC,
			durable=True,
		)
		await exchange.publish(
			Message(body=body, delivery_mode=DeliveryMode.PERSISTENT),
			routing_key=routing_key,
		)


async def run_outbox_worker_forever() -> None:
	while True:
		await outbox_crud.process_pending_batch(publish_message)
		await asyncio.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)


async def _handle_catalog_message(body: bytes) -> None:
	async with SessionLocal() as db:
		try:
			await catalog_sync_service.receive_message(
				db,
				body,
				sender_service=processed_catalog_event_crud.DEFAULT_SENDER_SERVICE,
			)
		except CatalogEventValidationError:
			await db.rollback()


async def run_catalog_consumer_forever() -> None:
	connection = await aio_pika.connect_robust(_rabbitmq_url())
	async with connection:
		channel = await connection.channel()
		await channel.set_qos(prefetch_count=10)
		exchange = await channel.declare_exchange(
			settings.RABBITMQ_EXCHANGE,
			ExchangeType.TOPIC,
			durable=True,
		)
		queue = await channel.declare_queue(CATALOG_EVENTS_QUEUE, durable=True)
		await queue.bind(exchange, routing_key=CATALOG_EVENTS_ROUTING_KEY)

		async with queue.iterator() as queue_iter:
			async for message in queue_iter:
				async with message.process(requeue=False):
					try:
						await _handle_catalog_message(message.body)
					except CatalogEventValidationError:
						pass
