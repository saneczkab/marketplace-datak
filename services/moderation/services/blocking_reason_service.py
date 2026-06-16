from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

import crud.blocking_reason as blocking_reason_crud
from database.models.blocking_reason import BlockingReason
from schemas.blocking_reason import (
	BlockingReasonCreateRequest,
	BlockingReasonResponse,
	BlockingReasonUpdateRequest,
)


def _build_blocking_reason_schema(reason: BlockingReason) -> BlockingReasonResponse:
	return BlockingReasonResponse(
		id=reason.id,
		code=reason.code,
		title=reason.title,
		description=reason.description,
		hard_block=reason.hard_block,
		is_active=reason.is_active,
	)


async def list_blocking_reasons(
	db: AsyncSession,
	hard_block: bool | None,
	is_active: bool,
) -> list[BlockingReasonResponse]:
	reasons = await blocking_reason_crud.list_reasons(
		db, hard_block=hard_block, is_active=is_active
	)
	return [_build_blocking_reason_schema(reason) for reason in reasons]


async def create_blocking_reason(
	db: AsyncSession, body: BlockingReasonCreateRequest
) -> BlockingReasonResponse:
	reason = await blocking_reason_crud.create(
		db,
		code=body.code,
		title=body.title,
		description=body.description,
		hard_block=body.hard_block,
	)
	return _build_blocking_reason_schema(reason)


async def update_blocking_reason(
	db: AsyncSession, reason_id: UUID, body: BlockingReasonUpdateRequest
) -> BlockingReasonResponse:
	reason = await blocking_reason_crud.update_by_id(
		db,
		reason_id,
		title=body.title,
		description=body.description,
		is_active=body.is_active,
	)
	return _build_blocking_reason_schema(reason)


async def deactivate_blocking_reason(db: AsyncSession, reason_id: UUID) -> None:
	await blocking_reason_crud.deactivate_by_id(db, reason_id)
