"""
Обработка входящих и исходящих сообщений RabbitMQ на уровне DB -> Rabbit или Rabbit -> DB
"""

from core.config import settings
from core.db import get_db_context
from crud import inbox as inbox_crud
from crud import outbox as outbox_crud
from database.models import InboxEvent, InboxEventStatusEnum, OutboxEventStatusEnum

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
from datetime import datetime
import json
import uuid
import logging
import asyncio


logger = logging.getLogger(__name__)

_connection = None
_channel = None
_exchange = None


async def get_connection() -> aio_pika.abc.AbstractRobustConnection:
	global _connection
	if _connection is None or _connection.is_closed:
		_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
	return _connection


async def get_channel() -> aio_pika.abc.AbstractRobustChannel:
	global _channel
	if _channel is None or _channel.is_closed:
		connection = await get_connection()
		_channel = await connection.channel()
	return _channel


async def get_exchange() -> aio_pika.abc.AbstractRobustExchange:
	global _exchange
	if _exchange is None:
		channel = await get_channel()
		_exchange = await channel.declare_exchange(
			settings.RABBITMQ_EXCHANGE, ExchangeType.TOPIC, durable=True
		)
	return _exchange


async def consume_and_store(
	queue_name: str,
	routing_keys: list[str],
) -> None:
	"""Collects all messages from queue `queue_name` and stores them in database

	Args:
		queue_name (str): queue to listen to
		routing_keys (list[str]): routing keys of messages that will be binded to that queue
	"""
	connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
	channel = await connection.channel()
	await channel.set_qos(prefetch_count=10)
	exchange = await channel.declare_exchange(
		settings.RABBITMQ_EXCHANGE, ExchangeType.TOPIC, durable=True
	)

	queue = await channel.declare_queue(queue_name, durable=True)

	for routing_key in routing_keys:
		await queue.bind(exchange, routing_key)

	async with queue.iterator() as queue_iter:
		async for message in queue_iter:
			async with message.process():
				logger.info("Processing new message")
				try:
					payload = json.loads(message.body)

					idempotency_key = uuid.UUID(payload["idempotency_key"])

					async with get_db_context() as db:
						existing = await inbox_crud.get_event_by_idempotency_key(
							idempotency_key, db
						)

						if existing:
							continue

						inbox_event = InboxEvent(
							idempotency_key=idempotency_key,
							routing_key=message.routing_key,
							payload=payload["payload"],
							event_type=payload["event_type"],
							occurred_at=datetime.fromisoformat(payload["occurred_at"]),
							status=InboxEventStatusEnum.PENDING,
						)
						await inbox_crud.add_event(inbox_event, db)
				except Exception as e:  # noqa
					logger.error(f"Error processing message: {e}")


async def run_consumer_forever() -> None:
	logger.info("Consumer started")
	await asyncio.gather(
		consume_and_store("product.catalog.updates", ["product.*"]),
		consume_and_store("orders.events", ["orders.*"]),
		run_outbox_publisher(),
	)


async def publish_message(routing_key: str, payload: dict) -> None:
	body = json.dumps(payload).encode("utf-8")
	exchange = await get_exchange()

	await exchange.publish(
		Message(body=body, delivery_mode=DeliveryMode.PERSISTENT),
		routing_key=routing_key,
	)


async def publish_outbox_events() -> None:
	from core.db import get_db_context

	async with get_db_context() as db:
		unsent_events = await outbox_crud.get_unsent_events(db, limit=100)

		for event in unsent_events:
			try:
				await publish_message(event.routing_key, event.payload)

				event.status = OutboxEventStatusEnum.SENT
				await outbox_crud.mark_event_sent(event, db)

				logger.info(f"Published outbox event {event.id}")

			except Exception as e:  # noqa
				logger.error(f"Failed to publish outbox event {event.id}: {e}")


async def run_outbox_publisher(interval_seconds: int = 5) -> None:
	logger.info("Outbox publisher started")

	while True:
		try:
			await publish_outbox_events()
		except Exception as e:  # noqa
			logger.error(f"Error in outbox publisher: {e}")

		await asyncio.sleep(interval_seconds)
