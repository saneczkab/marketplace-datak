"""
Обработка входящих и исходящих сообщений RabbitMQ на уровне DB -> Rabbit или Rabbit -> DB
"""

from core.config import settings
from core.db import get_db_context
from crud import inbox as inbox_crud
from database.models import InboxEvent, InboxEventStatusEnum

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
import json
import uuid


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
						payload=payload,
						event_type=payload["event_type"],
						occurred_at=message.occurred_at,
						status=InboxEventStatusEnum.PENDING,
					)
					await inbox_crud.add_event(inbox_event, db)


async def run_consumer_forever() -> None:
	await consume_and_store("product.catalog.updates", ["product.*"])


async def publish_message(routing_key: str, payload: dict) -> None:
	body = json.dumps(payload).encode("utf-8")

	connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
	# Do we really need to connect every time?
	# Probably creating connection object and passing it will be better
	# Probably right thing is to pass channel rather than connection

	async with connection:
		channel = await connection.channel()
		exchange = await channel.declare_exchange(
			settings.RABBITMQ_EXCHANGE, ExchangeType.TOPIC, durable=True
		)

		await exchange.publish(
			Message(body=body, delivery_mode=DeliveryMode.PERSISTENT),
			routing_key=routing_key,
		)
