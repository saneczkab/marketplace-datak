from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database.models.tickets.ticket import Ticket, TicketStatus
from exceptions.ticket import ModeratorAlreadyHasTicketInReviewError


async def release_expired_in_review(db: AsyncSession) -> None:
	cutoff = datetime.now(timezone.utc) - timedelta(
		minutes=settings.IN_REVIEW_CLAIM_TIMEOUT_MINUTES
	)
	await db.execute(
		update(Ticket)
		.where(
			Ticket.status == TicketStatus.IN_REVIEW,
			Ticket.claimed_at.isnot(None),
			Ticket.claimed_at < cutoff,
		)
		.values(
			status=TicketStatus.PENDING,
			assigned_moderator_id=None,
			claimed_at=None,
		)
	)
	await db.flush()


async def moderator_has_in_review(db: AsyncSession, moderator_id: UUID) -> bool:
	result = await db.execute(
		select(Ticket.id)
		.where(
			Ticket.assigned_moderator_id == moderator_id,
			Ticket.status == TicketStatus.IN_REVIEW,
		)
		.limit(1)
	)
	return result.scalar_one_or_none() is not None


async def claim_next_ticket(
	db: AsyncSession,
	moderator_id: UUID,
	queue_priority: int | None = None,
	category_ids: list[UUID] | None = None,
) -> Ticket | None:
	await release_expired_in_review(db)

	if await moderator_has_in_review(db, moderator_id):
		raise ModeratorAlreadyHasTicketInReviewError(
			"Moderator already has a ticket in review"
		)

	stmt = (
		select(Ticket)
		.where(Ticket.status == TicketStatus.PENDING)
		.order_by(Ticket.queue_priority.asc(), Ticket.created_at.asc())
		.limit(1)
		.with_for_update(skip_locked=True)
	)
	if queue_priority is not None:
		stmt = stmt.where(Ticket.queue_priority == queue_priority)
	if category_ids:
		stmt = stmt.where(Ticket.category_id.in_(category_ids))

	result = await db.execute(stmt)
	ticket = result.scalar_one_or_none()
	if ticket is None:
		await db.commit()
		return None

	now = datetime.now(timezone.utc)
	ticket.status = TicketStatus.IN_REVIEW
	ticket.assigned_moderator_id = moderator_id
	ticket.claimed_at = now
	db.add(ticket)
	await db.flush()
	await db.commit()
	await db.refresh(ticket)
	return ticket
