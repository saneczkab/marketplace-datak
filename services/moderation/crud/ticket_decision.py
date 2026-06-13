import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import blocking_reason as blocking_reason_crud
from crud import catalog as catalog_crud
from crud import outbox as outbox_crud
from crud import ticket as ticket_crud
from database.models.blocking_reason import BlockingReason
from database.models.tickets.ticket import Ticket, TicketStatus
from exceptions.ticket import (
	BlockingReasonNotFoundError,
	TicketHardBlockedError,
	TicketNoSkusError,
	TicketNotAssignedError,
	TicketNotFoundError,
	TicketWrongStatusError,
)
from schemas.moderation_event import (
	ModerationEventRequest,
	ModerationEventType,
	ModerationFieldReport,
)
from schemas.ticket import BlockFieldReport


def _primary_blocking_reason_id(reasons: list[BlockingReason], is_hard: bool) -> UUID:
	if is_hard:
		for reason in reasons:
			if reason.hard_block:
				return reason.id
	return reasons[0].id


def _event_field_reports(
	reports: list[BlockFieldReport],
) -> list[ModerationFieldReport]:
	return [
		ModerationFieldReport(
			field_name=report.field_path,
			sku_id=report.sku_id,
			comment=report.message,
		)
		for report in reports
	]


async def block_ticket(
	db: AsyncSession,
	ticket_id: UUID,
	moderator_id: UUID,
	blocking_reason_ids: list[UUID],
	comment: str | None,
	field_reports: list[BlockFieldReport],
) -> Ticket:
	ticket = await ticket_crud.lock_by_id(db, ticket_id)
	if ticket is None:
		raise TicketNotFoundError(f"Ticket {ticket_id} not found")

	if ticket.status == TicketStatus.HARD_BLOCKED:
		raise TicketHardBlockedError("Product is permanently blocked")

	if ticket.status != TicketStatus.IN_REVIEW:
		raise TicketWrongStatusError("Product is not in review status")

	if ticket.assigned_moderator_id != moderator_id:
		raise TicketNotAssignedError("This moderation card is not assigned to you")

	reasons = await blocking_reason_crud.get_active_by_ids(db, blocking_reason_ids)
	if len(reasons) != len(blocking_reason_ids):
		raise BlockingReasonNotFoundError("One or more blocking reasons not found")

	is_hard = any(reason.hard_block for reason in reasons)
	primary_reason_id = _primary_blocking_reason_id(reasons, is_hard)

	await ticket_crud.delete_field_reports(db, ticket.id)
	if is_hard:
		updated = await ticket_crud.mark_hard_blocked(
			db, ticket, moderator_id, primary_reason_id, comment
		)
	else:
		updated = await ticket_crud.mark_blocked(
			db, ticket, moderator_id, primary_reason_id, comment
		)
	if field_reports:
		await ticket_crud.insert_field_reports(db, ticket.id, field_reports)

	event_reports = _event_field_reports(field_reports) or None
	event = ModerationEventRequest(
		idempotency_key=uuid.uuid4(),
		product_id=ticket.product_id,
		event_type=ModerationEventType.BLOCKED,
		moderator_id=moderator_id,
		moderator_comment=comment,
		blocking_reason_id=primary_reason_id,
		hard_block=is_hard,
		field_reports=event_reports,
		occurred_at=datetime.now(timezone.utc),
	)
	await outbox_crud.enqueue_moderation_result(db, event)
	await db.commit()
	await db.refresh(updated)
	return updated


async def approve_ticket(
	db: AsyncSession,
	ticket_id: UUID,
	moderator_id: UUID,
	comment: str | None,
) -> Ticket:
	ticket = await ticket_crud.lock_by_id(db, ticket_id)
	if ticket is None:
		raise TicketNotFoundError(f"Ticket {ticket_id} not found")

	if ticket.status == TicketStatus.HARD_BLOCKED:
		raise TicketHardBlockedError("Product is permanently blocked")

	if ticket.status != TicketStatus.IN_REVIEW:
		raise TicketWrongStatusError("Product is not in review status")

	if ticket.assigned_moderator_id != moderator_id:
		raise TicketNotAssignedError("This moderation card is not assigned to you")

	snapshot = await catalog_crud.build_product_snapshot(db, ticket.product_id)
	if snapshot is None or not snapshot.skus:
		raise TicketNoSkusError("Product has no SKUs, cannot approve")

	await ticket_crud.delete_field_reports(db, ticket.id)
	updated = await ticket_crud.mark_approved(db, ticket, moderator_id, comment)

	event = ModerationEventRequest(
		idempotency_key=uuid.uuid4(),
		product_id=ticket.product_id,
		event_type=ModerationEventType.MODERATED,
		moderator_id=moderator_id,
		moderator_comment=comment,
		occurred_at=datetime.now(timezone.utc),
	)
	await outbox_crud.enqueue_moderation_result(db, event)
	await db.commit()
	await db.refresh(updated)
	return updated
