import asyncio
import json

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message

from core.config import settings
from core.db import SessionLocal
from crud import outbox as outbox_crud
from crud.moderation_event import DEFAULT_SENDER_SERVICE
from exceptions.moderation_event import ModerationEventValidationError
from exceptions.product import ProductNotFoundError
from services import moderation_event_service

MODERATION_EVENTS_QUEUE = "b2b.moderation.events"
MODERATION_RESULT_ROUTING_KEY = "b2b.moderation.result"


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


async def _handle_moderation_message(body: bytes) -> None:
	payload = json.loads(body.decode("utf-8"))
	async with SessionLocal() as db:
		try:
			await moderation_event_service.receive_moderation_event_payload(
				db,
				payload,
				sender_service=DEFAULT_SENDER_SERVICE,
			)
		except ProductNotFoundError:
			await db.rollback()
		except ModerationEventValidationError:
			await db.rollback()


async def run_moderation_consumer_forever() -> None:
	connection = await aio_pika.connect_robust(_rabbitmq_url())
	async with connection:
		channel = await connection.channel()
		await channel.set_qos(prefetch_count=10)
		exchange = await channel.declare_exchange(
			settings.RABBITMQ_EXCHANGE,
			ExchangeType.TOPIC,
			durable=True,
		)
		queue = await channel.declare_queue(MODERATION_EVENTS_QUEUE, durable=True)
		await queue.bind(exchange, routing_key=MODERATION_RESULT_ROUTING_KEY)

		async with queue.iterator() as queue_iter:
			async for message in queue_iter:
				async with message.process(requeue=False):
					try:
						await _handle_moderation_message(message.body)
					except json.JSONDecodeError:
						pass
