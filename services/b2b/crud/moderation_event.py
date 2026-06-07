from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud import outbox as outbox_crud
from crud import sku as sku_crud
from database.models.catalog.base import Product, ProductStatusEnum
from database.models.catalog.moderation_processed_events import ModerationProcessedEvent
from schemas.moderation_event import ModerationEventRequest, ModerationEventType

MODERATION_IDEMPOTENCY_TTL = timedelta(hours=24)
DEFAULT_SENDER_SERVICE = "moderation"


async def get_processed_event(
	db: AsyncSession, sender_service: str, idempotency_key: UUID
) -> ModerationProcessedEvent | None:
	result = await db.execute(
		select(ModerationProcessedEvent).where(
			ModerationProcessedEvent.sender_service == sender_service,
			ModerationProcessedEvent.idempotency_key == idempotency_key,
		)
	)
	return result.scalar_one_or_none()


async def delete_processed_event(
	db: AsyncSession, sender_service: str, idempotency_key: UUID
) -> None:
	await db.execute(
		delete(ModerationProcessedEvent).where(
			ModerationProcessedEvent.sender_service == sender_service,
			ModerationProcessedEvent.idempotency_key == idempotency_key,
		)
	)
	await db.flush()


def processed_event_is_valid(
	event: ModerationProcessedEvent, now: datetime | None = None
) -> bool:
	current = now or datetime.now(timezone.utc)
	processed_at = event.processed_at
	if processed_at.tzinfo is None:
		processed_at = processed_at.replace(tzinfo=timezone.utc)
	return current - processed_at < MODERATION_IDEMPOTENCY_TTL


async def lock_product(db: AsyncSession, product_id: UUID) -> Product | None:
	result = await db.execute(
		select(Product).where(Product.id == product_id).with_for_update()
	)
	return result.scalar_one_or_none()


def _clear_blocking_data(product: Product) -> None:
	product.blocked_reason_id = None
	product.blocking_reason_title = None
	product.moderator_comment = ""
	product.field_reports = []


def _apply_blocked(
	product: Product,
	request: ModerationEventRequest,
) -> None:
	product.blocked_reason_id = request.blocking_reason_id
	product.blocking_reason_title = None
	product.moderator_comment = request.moderator_comment or ""
	raw_reports = request.field_reports or []
	product.field_reports = [
		report.model_dump(mode="json", exclude_none=True) for report in raw_reports
	]
	if request.hard_block:
		product.status = ProductStatusEnum.HARD_BLOCKED
	else:
		product.status = ProductStatusEnum.BLOCKED


async def apply_moderation_event(
	db: AsyncSession,
	request: ModerationEventRequest,
	sender_service: str = DEFAULT_SENDER_SERVICE,
) -> bool:
	existing = await get_processed_event(db, sender_service, request.idempotency_key)
	if existing is not None:
		if processed_event_is_valid(existing):
			return False
		await delete_processed_event(db, sender_service, request.idempotency_key)

	product = await lock_product(db, request.product_id)
	if product is None:
		from exceptions.product import ProductNotFoundError

		raise ProductNotFoundError("Product not found")

	if request.event_type == ModerationEventType.MODERATED:
		product.status = ProductStatusEnum.MODERATED
		_clear_blocking_data(product)
	elif request.event_type == ModerationEventType.BLOCKED:
		_apply_blocked(product, request)
		skus = await sku_crud.get_by_product_id(db, product.id)
		await outbox_crud.enqueue_product_blocked(
			db,
			product_id=product.id,
			sku_ids=[sku.id for sku in skus],
			occurred_at=request.occurred_at,
		)

	db.add(product)
	db.add(
		ModerationProcessedEvent(
			sender_service=sender_service,
			idempotency_key=request.idempotency_key,
			product_id=request.product_id,
			event_type=request.event_type.value,
		)
	)
	await db.commit()
	return True
