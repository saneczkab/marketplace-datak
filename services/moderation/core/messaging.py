import aio_pika
from aio_pika import ExchangeType

from core.config import settings
from core.db import SessionLocal
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
