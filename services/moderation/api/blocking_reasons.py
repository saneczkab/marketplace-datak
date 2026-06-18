from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from exceptions.blocking_reason import (
	BlockingReasonCodeExistsError,
	BlockingReasonNotFoundError,
)
from schemas.blocking_reason import (
	BlockingReasonCreateRequest,
	BlockingReasonResponse,
	BlockingReasonUpdateRequest,
)
from services import blocking_reason_service

router = APIRouter(prefix="/blocking-reasons", tags=["BlockingReasons"])


@router.get("", response_model=list[BlockingReasonResponse])
async def list_blocking_reasons_endpoint(
	db: Annotated[AsyncSession, Depends(get_db)],
	hard_block: bool | None = None,
	is_active: Annotated[bool, Query()] = True,
) -> list[BlockingReasonResponse]:
	return await blocking_reason_service.list_blocking_reasons(
		db, hard_block=hard_block, is_active=is_active
	)


@router.post("", response_model=BlockingReasonResponse, status_code=201)
async def create_blocking_reason_endpoint(
	body: BlockingReasonCreateRequest,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> BlockingReasonResponse:
	try:
		return await blocking_reason_service.create_blocking_reason(db, body)
	except BlockingReasonCodeExistsError as exc:
		raise HTTPException(
			status_code=409,
			detail={"code": "CONFLICT", "message": str(exc)},
		) from exc


@router.patch("/{reason_id}", response_model=BlockingReasonResponse)
async def update_blocking_reason_endpoint(
	reason_id: UUID,
	body: BlockingReasonUpdateRequest,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> BlockingReasonResponse:
	try:
		return await blocking_reason_service.update_blocking_reason(db, reason_id, body)
	except BlockingReasonNotFoundError as exc:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(exc)},
		) from exc


@router.delete("/{reason_id}", status_code=204)
async def deactivate_blocking_reason_endpoint(
	reason_id: UUID,
	db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
	try:
		await blocking_reason_service.deactivate_blocking_reason(db, reason_id)
	except BlockingReasonNotFoundError as exc:
		raise HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": str(exc)},
		) from exc
	return Response(status_code=204)
