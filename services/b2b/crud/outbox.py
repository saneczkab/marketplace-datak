import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import SessionLocal
from database.models.event.outbox import OutboxEvent, OutboxEventStatus

PublishFn = Callable[[str, dict], Awaitable[None]]

MODERATION_PRODUCT_CREATED = "moderation.product.created"
MODERATION_PRODUCT_DELETED = "moderation.product.deleted"
B2C_EVENT_ROUTING_KEY = "b2c.events"
B2C_PRODUCT_DELETED = "b2c.product.deleted"
PRODUCT_BLOCKED_EVENT_TYPE = "PRODUCT_BLOCKED"
B2C_SKU_OUT_OF_STOCK = "SKU_OUT_OF_STOCK"


def build_moderation_product_created_payload(
	product_id: UUID,
	seller_id: UUID,
	idempotency_key: UUID,
	event: str = "CREATED",
) -> dict:
	occurred_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
	return {
		"idempotency_key": str(idempotency_key),
		"product_id": str(product_id),
		"seller_id": str(seller_id),
		"event": event,
		"date": occurred_at,
	}


def build_moderation_product_deleted_payload(
	product_id: UUID,
	seller_id: UUID,
	idempotency_key: UUID,
	event: str = "DELETED",
) -> dict:
	occurred_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
	return {
		"idempotency_key": str(idempotency_key),
		"product_id": str(product_id),
		"seller_id": str(seller_id),
		"event": event,
		"date": occurred_at,
	}


def build_b2c_product_deleted_payload(
	product_id: UUID,
	sku_ids: list[UUID],
	idempotency_key: UUID,
	event: str = "PRODUCT_DELETED",
) -> dict:
	occurred_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
	return {
		"idempotency_key": str(idempotency_key),
		"product_id": str(product_id),
		"sku_ids": [str(sku_id) for sku_id in sku_ids],
		"event": event,
		"date": occurred_at,
	}


async def enqueue_b2c_event(db: AsyncSession, message: dict) -> OutboxEvent:
	outbox_event = OutboxEvent(
		idempotency_key=UUID(message["idempotency_key"]),
		event_type=message["event_type"],
		routing_key=B2C_EVENT_ROUTING_KEY,
		payload=message,
		status=OutboxEventStatus.PENDING,
	)
	db.add(outbox_event)
	await db.flush()
	return outbox_event


def build_product_blocked_payload(
	product_id: UUID,
	sku_ids: list[UUID],
	occurred_at: datetime | None = None,
) -> dict:
	when = occurred_at or datetime.now(timezone.utc)
	if when.tzinfo is None:
		when = when.replace(tzinfo=timezone.utc)
	return {
		"event_type": PRODUCT_BLOCKED_EVENT_TYPE,
		"idempotency_key": str(uuid.uuid4()),
		"occurred_at": when.isoformat().replace("+00:00", "Z"),
		"payload": {
			"product_id": str(product_id),
			"sku_ids": [str(sku_id) for sku_id in sku_ids],
		},
	}


async def enqueue_product_blocked(
	db: AsyncSession,
	product_id: UUID,
	sku_ids: list[UUID],
	occurred_at: datetime | None = None,
) -> OutboxEvent:
	message = build_product_blocked_payload(product_id, sku_ids, occurred_at)
	return await enqueue_b2c_event(db, message)


async def enqueue_moderation_product_created(
	db: AsyncSession,
	product_id: UUID,
	seller_id: UUID,
	event: str = "CREATED",
) -> OutboxEvent:
	idempotency_key = uuid.uuid4()
	payload = build_moderation_product_created_payload(
		product_id=product_id,
		seller_id=seller_id,
		idempotency_key=idempotency_key,
		event=event,
	)
	outbox_event = OutboxEvent(
		idempotency_key=idempotency_key,
		event_type=MODERATION_PRODUCT_CREATED,
		routing_key=MODERATION_PRODUCT_CREATED,
		payload=payload,
		status=OutboxEventStatus.PENDING,
	)
	db.add(outbox_event)
	await db.flush()
	return outbox_event


async def enqueue_moderation_product_deleted(
	db: AsyncSession,
	product_id: UUID,
	seller_id: UUID,
) -> OutboxEvent:
	idempotency_key = uuid.uuid4()
	payload = build_moderation_product_deleted_payload(
		product_id=product_id,
		seller_id=seller_id,
		idempotency_key=idempotency_key,
	)
	outbox_event = OutboxEvent(
		idempotency_key=idempotency_key,
		event_type=MODERATION_PRODUCT_DELETED,
		routing_key=MODERATION_PRODUCT_DELETED,
		payload=payload,
		status=OutboxEventStatus.PENDING,
	)
	db.add(outbox_event)
	await db.flush()
	return outbox_event


async def enqueue_b2c_product_deleted(
	db: AsyncSession,
	product_id: UUID,
	sku_ids: list[UUID],
) -> OutboxEvent:
	idempotency_key = uuid.uuid4()
	payload = build_b2c_product_deleted_payload(
		product_id=product_id,
		sku_ids=sku_ids,
		idempotency_key=idempotency_key,
	)
	outbox_event = OutboxEvent(
		idempotency_key=idempotency_key,
		event_type=B2C_PRODUCT_DELETED,
		routing_key=B2C_EVENT_ROUTING_KEY,
		payload=payload,
		status=OutboxEventStatus.PENDING,
	)
	db.add(outbox_event)
	await db.flush()
	return outbox_event


def build_b2c_sku_out_of_stock_payload(
	sku_id: UUID,
	product_id: UUID,
	available_quantity: int = 0,
) -> dict:
	return {
		"event_type": B2C_SKU_OUT_OF_STOCK,
		"idempotency_key": str(uuid.uuid4()),
		"occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
		"payload": {
			"sku_id": str(sku_id),
			"product_id": str(product_id),
			"available_quantity": available_quantity,
		},
	}


async def enqueue_b2c_sku_out_of_stock(
	db: AsyncSession,
	sku_id: UUID,
	product_id: UUID,
	available_quantity: int = 0,
) -> OutboxEvent:
	message = build_b2c_sku_out_of_stock_payload(sku_id, product_id, available_quantity)
	return await enqueue_b2c_event(db, message)


async def fetch_pending_events(db: AsyncSession, limit: int = 50) -> list[OutboxEvent]:
	result = await db.execute(
		select(OutboxEvent)
		.where(OutboxEvent.status == OutboxEventStatus.PENDING)
		.order_by(OutboxEvent.created_at)
		.limit(limit)
	)
	return list(result.scalars().all())


async def get_pending_event_by_id(
	db: AsyncSession, event_id: UUID
) -> OutboxEvent | None:
	event = await db.get(OutboxEvent, event_id)
	if event is None or event.status != OutboxEventStatus.PENDING:
		return None
	return event


async def mark_event_sent(db: AsyncSession, event: OutboxEvent) -> None:
	event.status = OutboxEventStatus.SENT
	event.sent_at = datetime.now(timezone.utc)
	db.add(event)
	await db.commit()


async def deliver_pending_event(
	db: AsyncSession,
	event_id: UUID,
	publish: PublishFn,
) -> bool:
	db_event = await get_pending_event_by_id(db, event_id)
	if db_event is None:
		return False
	try:
		await publish(db_event.routing_key, db_event.payload)
		await mark_event_sent(db, db_event)
		return True
	except Exception:  # noqa
		await db.rollback()
		return False


async def process_pending_batch(publish: PublishFn, limit: int = 50) -> int:
	processed = 0
	async with SessionLocal() as db:
		events = await fetch_pending_events(db, limit=limit)

	for event in events:
		async with SessionLocal() as db:
			if await deliver_pending_event(db, event.id, publish):
				processed += 1
	return processed
