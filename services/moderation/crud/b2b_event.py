from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import catalog as catalog_crud
from crud import processed_event as processed_event_crud
from crud import ticket as ticket_crud
from database.models.tickets.ticket import TicketKind, TicketStatus
from exceptions.b2b_event import TicketAlreadyExistsError, TicketNotFoundError
from exceptions.catalog import CatalogProductNotFoundError
from schemas.b2b_event import (
	B2BEventType,
	EventProductCreatedPayload,
	EventProductDeletedPayload,
	EventProductEditedPayload,
	IncomingB2BEvent,
)
from schemas.product_snapshot import ProductSnapshot

DEFAULT_SENDER_SERVICE = processed_event_crud.DEFAULT_SENDER_SERVICE


def _compute_queue_priority(
	old_status: TicketStatus,
	total_qty: int,
	current_priority: int,
) -> int:
	if old_status == TicketStatus.BLOCKED:
		return 2
	if old_status == TicketStatus.APPROVED:
		return 3 if total_qty > 0 else 4
	return current_priority


async def _load_product_snapshot(db: AsyncSession, product_id: UUID) -> ProductSnapshot:
	snapshot = await catalog_crud.build_product_snapshot(db, product_id)
	if snapshot is None:
		raise CatalogProductNotFoundError(
			f"Product {product_id} not found in local catalog replica"
		)
	return snapshot


def _product_id_from_event(event: IncomingB2BEvent) -> UUID:
	payload = event.payload
	if isinstance(payload, EventProductCreatedPayload):
		return payload.product_id
	if isinstance(payload, EventProductEditedPayload):
		return payload.product_id
	return payload.product_id


async def _handle_product_created(db: AsyncSession, event: IncomingB2BEvent) -> None:
	payload = event.payload
	if not isinstance(payload, EventProductCreatedPayload):
		return
	existing = await ticket_crud.get_by_product_id(db, payload.product_id)
	if existing is not None:
		if existing.status == TicketStatus.HARD_BLOCKED:
			return
		raise TicketAlreadyExistsError(
			f"Ticket already exists for product {payload.product_id}"
		)

	snapshot = await _load_product_snapshot(db, payload.product_id)
	await ticket_crud.create_ticket(
		db,
		product_id=payload.product_id,
		seller_id=payload.seller_id,
		category_id=payload.category_id,
		kind=TicketKind.CREATE,
		status=TicketStatus.PENDING,
		queue_priority=1,
		total_active_quantity=sum(sku.active_quantity for sku in snapshot.skus),
		json_before=None,
		json_after=snapshot,
	)


async def _handle_product_edited(db: AsyncSession, event: IncomingB2BEvent) -> None:
	payload = event.payload
	if not isinstance(payload, EventProductEditedPayload):
		return
	ticket = await ticket_crud.lock_by_product_id(db, payload.product_id)
	if ticket is None:
		raise TicketNotFoundError(f"No ticket found for product {payload.product_id}")
	if ticket.status == TicketStatus.HARD_BLOCKED:
		return

	old_status = ticket.status
	current_priority = ticket.queue_priority
	snapshot = await _load_product_snapshot(db, payload.product_id)
	qty = sum(sku.active_quantity for sku in snapshot.skus)
	new_priority = _compute_queue_priority(old_status, qty, current_priority)

	await ticket_crud.delete_field_reports(db, ticket.id)
	await ticket_crud.update_ticket(
		db,
		ticket,
		seller_id=payload.seller_id,
		category_id=payload.category_id,
		kind=TicketKind.EDIT,
		status=TicketStatus.PENDING,
		queue_priority=new_priority,
		total_active_quantity=qty,
		json_before=ticket.json_after,
		json_after=snapshot,
		clear_moderator=True,
	)


async def _handle_product_deleted(db: AsyncSession, event: IncomingB2BEvent) -> None:
	payload = event.payload
	if not isinstance(payload, EventProductDeletedPayload):
		return
	ticket = await ticket_crud.get_by_product_id(db, payload.product_id)
	if ticket is None:
		return
	await ticket_crud.delete_ticket(db, ticket)


async def apply_b2b_event(
	db: AsyncSession,
	event: IncomingB2BEvent,
	sender_service: str = DEFAULT_SENDER_SERVICE,
) -> bool:
	existing = await processed_event_crud.get_processed_event(
		db, sender_service, event.idempotency_key
	)
	if existing is not None:
		if processed_event_crud.processed_event_is_valid(existing):
			return False
		await processed_event_crud.delete_processed_event(
			db, sender_service, event.idempotency_key
		)

	product_id = _product_id_from_event(event)

	if event.event_type == B2BEventType.PRODUCT_CREATED:
		await _handle_product_created(db, event)
	elif event.event_type == B2BEventType.PRODUCT_EDITED:
		await _handle_product_edited(db, event)
	else:
		await _handle_product_deleted(db, event)

	await processed_event_crud.record_processed_event(
		db,
		sender_service=sender_service,
		idempotency_key=event.idempotency_key,
		product_id=product_id,
		event_type=event.event_type.value,
	)
	await db.commit()
	return True
