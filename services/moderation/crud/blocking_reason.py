from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.blocking_reason import BlockingReason
from exceptions.blocking_reason import (
	BlockingReasonCodeExistsError,
	BlockingReasonNotFoundError,
)


async def list_reasons(
	db: AsyncSession,
	hard_block: bool | None = None,
	is_active: bool = True,
) -> list[BlockingReason]:
	stmt = (
		select(BlockingReason)
		.where(BlockingReason.is_active.is_(is_active))
		.order_by(BlockingReason.title)
	)
	if hard_block is not None:
		stmt = stmt.where(BlockingReason.hard_block.is_(hard_block))
	result = await db.execute(stmt)
	return list(result.scalars().all())


async def get_by_id(db: AsyncSession, reason_id: UUID) -> BlockingReason | None:
	result = await db.execute(
		select(BlockingReason).where(BlockingReason.id == reason_id)
	)
	return result.scalar_one_or_none()


async def get_active_by_ids(
	db: AsyncSession, reason_ids: list[UUID]
) -> list[BlockingReason]:
	if not reason_ids:
		return []
	result = await db.execute(
		select(BlockingReason).where(
			BlockingReason.id.in_(reason_ids),
			BlockingReason.is_active.is_(True),
		)
	)
	reasons = list(result.scalars().all())
	reason_map = {reason.id: reason for reason in reasons}
	return [
		reason_map[reason_id] for reason_id in reason_ids if reason_id in reason_map
	]


async def create(
	db: AsyncSession,
	code: str,
	title: str,
	description: str | None,
	hard_block: bool,
) -> BlockingReason:
	existing = await db.execute(
		select(BlockingReason).where(BlockingReason.code == code)
	)
	if existing.scalar_one_or_none() is not None:
		raise BlockingReasonCodeExistsError("Blocking reason code already exists")

	reason = BlockingReason(
		code=code,
		title=title,
		description=description,
		hard_block=hard_block,
		is_active=True,
	)
	db.add(reason)
	await db.commit()
	await db.refresh(reason)
	return reason


async def update_by_id(
	db: AsyncSession,
	reason_id: UUID,
	title: str | None = None,
	description: str | None = None,
	is_active: bool | None = None,
) -> BlockingReason:
	reason = await get_by_id(db, reason_id)
	if reason is None:
		raise BlockingReasonNotFoundError(f"Blocking reason {reason_id} not found")

	if title is not None:
		reason.title = title
	if description is not None:
		reason.description = description
	if is_active is not None:
		reason.is_active = is_active

	await db.commit()
	await db.refresh(reason)
	return reason


async def deactivate_by_id(db: AsyncSession, reason_id: UUID) -> None:
	reason = await get_by_id(db, reason_id)
	if reason is None:
		raise BlockingReasonNotFoundError(f"Blocking reason {reason_id} not found")

	reason.is_active = False
	await db.commit()
