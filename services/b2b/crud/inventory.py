from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from crud import outbox as outbox_crud
from database.models import Sku
from database.models.catalog.base import Product
from database.models.catalog.inventory_operations import (
	InventoryReserveOperation,
	InventoryUnreserveOperation,
	InventoryFulfillOperation,
)

RESERVE_IDEMPOTENCY_TTL = timedelta(hours=1)


async def get_reserve_operation(
	db: AsyncSession, idempotency_key: UUID
) -> InventoryReserveOperation | None:
	result = await db.execute(
		select(InventoryReserveOperation).where(
			InventoryReserveOperation.idempotency_key == idempotency_key
		)
	)
	return result.scalar_one_or_none()


async def delete_reserve_operation(db: AsyncSession, idempotency_key: UUID) -> None:
	await db.execute(
		delete(InventoryReserveOperation).where(
			InventoryReserveOperation.idempotency_key == idempotency_key
		)
	)
	await db.flush()


async def get_unreserve_operation(
	db: AsyncSession, order_id: UUID
) -> InventoryUnreserveOperation | None:
	result = await db.execute(
		select(InventoryUnreserveOperation).where(
			InventoryUnreserveOperation.order_id == order_id
		)
	)
	return result.scalar_one_or_none()


async def lock_skus_with_products(
	db: AsyncSession, sku_ids: list[UUID]
) -> list[tuple[Sku, Product]]:
	ordered_ids = sorted(sku_ids)
	result = await db.execute(
		select(Sku, Product)
		.join(Product, Sku.product_id == Product.id)
		.where(Sku.id.in_(ordered_ids))
		.order_by(Sku.id)
		.with_for_update()
	)
	rows = list(result.all())
	by_id = {sku.id: (sku, product) for sku, product in rows}
	return [by_id[sku_id] for sku_id in ordered_ids if sku_id in by_id]


async def save_reserve(
	db: AsyncSession,
	idempotency_key: UUID,
	order_id: UUID,
	result: dict,
	outbox_payloads: list[dict],
) -> None:
	for message in outbox_payloads:
		await outbox_crud.enqueue_b2c_event(db, message)
	db.add(
		InventoryReserveOperation(
			idempotency_key=idempotency_key,
			order_id=order_id,
			result=result,
		)
	)
	await db.commit()


async def save_unreserve(
	db: AsyncSession,
	order_id: UUID,
	processed_at: datetime,
) -> None:
	db.add(InventoryUnreserveOperation(order_id=order_id, processed_at=processed_at))
	await db.commit()


async def get_fulfill_operation(
	db: AsyncSession, order_id: UUID
) -> InventoryFulfillOperation | None:
	result = await db.execute(
		select(InventoryFulfillOperation).where(
			InventoryFulfillOperation.order_id == order_id
		)
	)
	return result.scalar_one_or_none()


async def save_fulfill(
	db: AsyncSession,
	order_id: UUID,
	processed_at: datetime,
) -> None:
	db.add(InventoryFulfillOperation(order_id=order_id, processed_at=processed_at))
	await db.commit()


def reserve_operation_is_valid(
	operation: InventoryReserveOperation, now: datetime | None = None
) -> bool:
	current = now or datetime.now(timezone.utc)
	created = operation.created_at
	if created.tzinfo is None:
		created = created.replace(tzinfo=timezone.utc)
	return current - created < RESERVE_IDEMPOTENCY_TTL
