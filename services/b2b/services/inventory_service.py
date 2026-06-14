import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import inventory as inventory_crud
from database.models.catalog.base import ProductStatusEnum
from exceptions.inventory import (
	FulfillConflictError,
	InventoryValidationError,
	ReserveConflictError,
	UnreserveConflictError,
)
from exceptions.sku import SkuNotFoundError
from schemas.inventory import (
	FulfillRequest,
	FulfillResponse,
	InventoryOrderRequest,
	InventoryOrderResponse,
	InventoryItem,
	ReserveRequest,
	ReserveResponse,
)


def _build_b2c_sku_out_of_stock_message(
	sku_id: UUID, product_id: UUID, available_quantity: int
) -> dict:
	return {
		"event_type": "SKU_OUT_OF_STOCK",
		"idempotency_key": str(uuid.uuid4()),
		"occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
		"payload": {
			"sku_id": str(sku_id),
			"product_id": str(product_id),
			"available_quantity": available_quantity,
		},
	}


def _collect_reserve_failures(
	rows: list[tuple],
	quantities: dict[UUID, int],
) -> list[dict]:
	failed: list[dict] = []
	for sku, product in rows:
		if product.deleted or product.status != ProductStatusEnum.MODERATED:
			failed.append(
				{
					"sku_id": str(sku.id),
					"requested": quantities[sku.id],
					"available": sku.active_quantity,
					"reason": "PRODUCT_UNAVAILABLE",
				}
			)
			continue
		requested = quantities[sku.id]
		if sku.active_quantity < requested:
			reason = (
				"OUT_OF_STOCK" if sku.active_quantity == 0 else "INSUFFICIENT_STOCK"
			)
			failed.append(
				{
					"sku_id": str(sku.id),
					"requested": requested,
					"available": sku.active_quantity,
					"reason": reason,
				}
			)
	return failed


def _ensure_unique_sku_ids(items: list[InventoryItem]) -> dict[UUID, int]:
	quantities: dict[UUID, int] = {}
	for item in items:
		if item.sku_id in quantities:
			raise InventoryValidationError("Duplicate sku_id in items")
		quantities[item.sku_id] = item.quantity
	return quantities


async def reserve_inventory(
	db: AsyncSession, request: ReserveRequest
) -> ReserveResponse:
	quantities = _ensure_unique_sku_ids(request.items)
	sku_ids = list(quantities.keys())

	existing = await inventory_crud.get_reserve_operation(db, request.idempotency_key)
	if existing is not None:
		if inventory_crud.reserve_operation_is_valid(existing):
			stored = existing.result
			return ReserveResponse(
				order_id=UUID(stored["order_id"]),
				status=stored["status"],
				reserved_at=datetime.fromisoformat(
					stored["reserved_at"].replace("Z", "+00:00")
				),
			)
		await inventory_crud.delete_reserve_operation(db, request.idempotency_key)

	rows = await inventory_crud.lock_skus_with_products(db, sku_ids)
	if len(rows) != len(sku_ids):
		found = {sku.id for sku, _ in rows}
		missing = next(sid for sid in sku_ids if sid not in found)
		raise SkuNotFoundError(f"SKU with id {missing} not found")

	failed = _collect_reserve_failures(rows, quantities)
	if failed:
		await db.rollback()
		raise ReserveConflictError(failed)

	outbox_messages: list[dict] = []
	for sku, product in rows:
		requested = quantities[sku.id]
		sku.active_quantity -= requested
		sku.reserved_quantity += requested
		if sku.active_quantity == 0:
			outbox_messages.append(
				_build_b2c_sku_out_of_stock_message(
					sku.id, product.id, sku.active_quantity
				)
			)

	reserved_at = datetime.now(timezone.utc)
	response = ReserveResponse(
		order_id=request.order_id,
		status="RESERVED",
		reserved_at=reserved_at,
	)
	result = {
		"order_id": str(request.order_id),
		"status": response.status,
		"reserved_at": reserved_at.isoformat(),
	}
	await inventory_crud.save_reserve(
		db,
		request.idempotency_key,
		request.order_id,
		result,
		outbox_messages,
	)
	return response


async def unreserve_inventory(
	db: AsyncSession, request: InventoryOrderRequest
) -> InventoryOrderResponse:
	quantities = _ensure_unique_sku_ids(request.items)
	sku_ids = list(quantities.keys())

	existing = await inventory_crud.get_unreserve_operation(db, request.order_id)
	if existing is not None:
		processed_at = existing.processed_at
		if processed_at.tzinfo is None:
			processed_at = processed_at.replace(tzinfo=timezone.utc)
		return InventoryOrderResponse(
			order_id=request.order_id,
			status="UNRESERVED",
			processed_at=processed_at,
		)

	rows = await inventory_crud.lock_skus_with_products(db, sku_ids)
	if len(rows) != len(sku_ids):
		found = {sku.id for sku, _ in rows}
		missing = next(sid for sid in sku_ids if sid not in found)
		raise SkuNotFoundError(f"SKU with id {missing} not found")

	for sku, _product in rows:
		requested = quantities[sku.id]
		if sku.reserved_quantity < requested:
			await db.rollback()
			raise UnreserveConflictError(
				f"SKU {sku.id} has reserved_quantity {sku.reserved_quantity}, "
				f"cannot unreserve {requested}"
			)

	for sku, _product in rows:
		requested = quantities[sku.id]
		sku.active_quantity += requested
		sku.reserved_quantity -= requested

	processed_at = datetime.now(timezone.utc)
	await inventory_crud.save_unreserve(db, request.order_id, processed_at)
	return InventoryOrderResponse(
		order_id=request.order_id,
		status="UNRESERVED",
		processed_at=processed_at,
	)


async def fulfill_inventory(
	db: AsyncSession, request: FulfillRequest
) -> FulfillResponse:
	quantities = _ensure_unique_sku_ids(request.items)
	sku_ids = list(quantities.keys())

	existing = await inventory_crud.get_fulfill_operation(db, request.order_id)
	if existing is not None:
		return FulfillResponse(ok=True)

	rows = await inventory_crud.lock_skus_with_products(db, sku_ids)
	if len(rows) != len(sku_ids):
		found = {sku.id for sku, _ in rows}
		missing = next(sid for sid in sku_ids if sid not in found)
		raise SkuNotFoundError(f"SKU with id {missing} not found")

	for sku, _product in rows:
		requested = quantities[sku.id]
		if sku.reserved_quantity < requested:
			await db.rollback()
			raise FulfillConflictError(
				f"SKU {sku.id} has reserved_quantity {sku.reserved_quantity}, "
				f"cannot fulfill {requested}"
			)

	for sku, _product in rows:
		sku.reserved_quantity -= quantities[sku.id]

	processed_at = datetime.now(timezone.utc)
	await inventory_crud.save_fulfill(db, request.order_id, processed_at)
	return FulfillResponse(ok=True)
