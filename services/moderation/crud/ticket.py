from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.tickets.field_report import TicketFieldReport
from database.models.tickets.ticket import Ticket, TicketKind, TicketStatus
from schemas.product_snapshot import ProductSnapshot


def _snapshot_to_json(snapshot: ProductSnapshot | dict | None) -> dict | None:
	if snapshot is None:
		return None
	if isinstance(snapshot, dict):
		return snapshot
	return snapshot.model_dump(mode="json")


async def get_by_product_id(db: AsyncSession, product_id: UUID) -> Ticket | None:
	result = await db.execute(select(Ticket).where(Ticket.product_id == product_id))
	return result.scalar_one_or_none()


async def lock_by_product_id(db: AsyncSession, product_id: UUID) -> Ticket | None:
	result = await db.execute(
		select(Ticket).where(Ticket.product_id == product_id).with_for_update()
	)
	return result.scalar_one_or_none()


async def create_ticket(
	db: AsyncSession,
	product_id: UUID,
	seller_id: UUID,
	category_id: UUID | None,
	kind: TicketKind,
	status: TicketStatus,
	queue_priority: int,
	total_active_quantity: int,
	json_before: ProductSnapshot | None,
	json_after: ProductSnapshot,
) -> Ticket:
	ticket = Ticket(
		product_id=product_id,
		seller_id=seller_id,
		category_id=category_id,
		kind=kind,
		status=status,
		queue_priority=queue_priority,
		total_active_quantity=total_active_quantity,
		json_before=_snapshot_to_json(json_before),
		json_after=_snapshot_to_json(json_after),
	)
	db.add(ticket)
	await db.flush()
	return ticket


async def update_ticket(
	db: AsyncSession,
	ticket: Ticket,
	seller_id: UUID | None = None,
	category_id: UUID | None = None,
	kind: TicketKind | None = None,
	status: TicketStatus | None = None,
	queue_priority: int | None = None,
	total_active_quantity: int | None = None,
	json_before: ProductSnapshot | dict | None = None,
	json_after: ProductSnapshot | None = None,
	clear_moderator: bool = False,
) -> Ticket:
	if seller_id is not None:
		ticket.seller_id = seller_id
	if category_id is not None:
		ticket.category_id = category_id
	if kind is not None:
		ticket.kind = kind
	if status is not None:
		ticket.status = status
	if queue_priority is not None:
		ticket.queue_priority = queue_priority
	if total_active_quantity is not None:
		ticket.total_active_quantity = total_active_quantity
	if json_before is not None:
		ticket.json_before = _snapshot_to_json(json_before)
	if json_after is not None:
		ticket.json_after = _snapshot_to_json(json_after)
	if clear_moderator:
		ticket.assigned_moderator_id = None
	db.add(ticket)
	await db.flush()
	return ticket


async def delete_ticket(db: AsyncSession, ticket: Ticket) -> None:
	await db.delete(ticket)
	await db.flush()


async def delete_field_reports(db: AsyncSession, ticket_id: UUID) -> None:
	await db.execute(
		delete(TicketFieldReport).where(TicketFieldReport.ticket_id == ticket_id)
	)
	await db.flush()


async def get_ticket_with_reports(db: AsyncSession, product_id: UUID) -> Ticket | None:
	result = await db.execute(
		select(Ticket)
		.options(selectinload(Ticket.field_reports))
		.where(Ticket.product_id == product_id)
	)
	return result.scalar_one_or_none()
