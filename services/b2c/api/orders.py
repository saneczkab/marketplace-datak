from typing import Annotated

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from exceptions.order import (
	AddressNotFoundError,
	EmptyCartError,
	IdempotencyConflictError,
	InvalidIdempotencyKeyError,
	PaymentMethodNotFoundError,
	ReserveFailedError,
)
from schemas.order import OrderCreateRequest, OrderResponse
from services import order_service


router = fastapi.APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post(
	"",
	status_code=201,
	response_model=OrderResponse,
)
async def create_order(
	request: fastapi.Request,
	body: OrderCreateRequest,
	idempotency_key: Annotated[str, fastapi.Header(alias="Idempotency-Key")],
	db_session: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> OrderResponse:
	try:
		key_uuid = order_service.parse_idempotency_key(idempotency_key)
	except InvalidIdempotencyKeyError as err:
		raise fastapi.HTTPException(
			status_code=400,
			detail={
				"code": "BAD_REQUEST",
				"message": "Idempotency-Key must be a valid UUID",
			},
		) from err

	buyer_id_raw = getattr(request.state, "user_id", None)
	if not buyer_id_raw:
		raise fastapi.HTTPException(
			status_code=401,
			detail={
				"code": "UNAUTHORIZED",
				"message": "Missing or invalid Authorization header",
			},
		)
	buyer_id = order_service.parse_idempotency_key(str(buyer_id_raw))
	body_dump = body.model_dump(mode="json")

	try:
		result = await order_service.checkout(
			db_session,
			buyer_id=buyer_id,
			idempotency_key=key_uuid,
			body_raw=body_dump,
			address_id=body.address_id,
			payment_method_id=body.payment_method_id,
			comment=body.comment,
			items_snapshot=[
				item.model_dump(mode="json") for item in body.items_snapshot
			]
			if body.items_snapshot is not None
			else None,
		)
	except EmptyCartError as err:
		raise fastapi.HTTPException(
			status_code=400,
			detail={"code": "BAD_REQUEST", "message": "Cart is empty"},
		) from err
	except AddressNotFoundError as err:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": "Address not found"},
		) from err
	except PaymentMethodNotFoundError as err:
		raise fastapi.HTTPException(
			status_code=404,
			detail={"code": "NOT_FOUND", "message": "Payment method not found"},
		) from err
	except IdempotencyConflictError as err:
		raise fastapi.HTTPException(
			status_code=409,
			detail={
				"code": "IDEMPOTENCY_CONFLICT",
				"message": "Idempotency key already used with different request body",
			},
		) from err
	except ReserveFailedError as err:
		raise fastapi.HTTPException(
			status_code=409,
			detail={
				"code": "RESERVE_FAILED",
				"message": "Failed to reserve items",
			},
		) from err

	return result
