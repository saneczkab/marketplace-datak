from core.config import settings
import crud.events as events_crud

from database.models import InboxEvent, InboxEventStatusEnum

import aio_pika
from aio_pika import ExchangeType
from sqlalchemy.ext.asyncio import AsyncSession
import json
import uuid


def _rabbitmq_url() -> str:
	return (
		f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
		f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
	)


async def consume_and_store(
	queue_name: str, routing_keys: list[str], db: AsyncSession
) -> None:
	connection = await aio_pika.connect_robust(_rabbitmq_url())
	channel = await connection.channel()
	await channel.set_qos(prefetch_count=10)

	exchange = await channel.declare_exchange(
		settings.RABBITMQ_EXCHANGE, ExchangeType.TOPIC, durable=True
	)

	queue = await channel.declare_queue(queue_name, durable=True)

	for routing_key in routing_keys:
		await queue.bind(exchange, routing_key=routing_key)

	async with queue.iterator() as queue_iter:
		async for message in queue_iter:
			async with message.process():  # Auto-ACK после блока
				payload = json.loads(message.body)

				idempotency_key = uuid.UUID(payload["idempotency_key"])

				existing = await events_crud.get_event_by_idempotency_eky(
					idempotency_key, db
				)

				if existing:
					continue

				inbox_event = InboxEvent(
					id=uuid.uuid4(),
					idempotency_key=idempotency_key,
					routing_key=message.routing_key,
					payload=payload,
					status=InboxEventStatusEnum.PENDING,
				)
				await events_crud.add_event(inbox_event, db)


async def run_consumer_forever() -> None:
	await consume_and_store(
		queue_name="b2b.products",
		routing_keys=["moderation.product.approved", "moderation.product.rejected"],
	)
