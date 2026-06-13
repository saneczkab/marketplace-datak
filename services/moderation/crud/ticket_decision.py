import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud import catalog as catalog_crud
from crud import outbox as outbox_crud
from crud import ticket as ticket_crud
from database.models.tickets.ticket import Ticket, TicketStatus
from exceptions.ticket import (
	TicketHardBlockedError,
	TicketNoSkusError,
	TicketNotAssignedError,
	TicketNotFoundError,
	TicketWrongStatusError,
)
from schemas.moderation_event import ModerationEventRequest, ModerationEventType


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
