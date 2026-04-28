import uuid
from typing import Annotated, Optional

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from schemas.cart import CartResponse
from services import cart_service

router = fastapi.APIRouter(prefix="/api/v1/cart", tags=["Корзина"])


def validate_cart_identity(
	x_user_id: Optional[str] = fastapi.Header(None, alias="X-User-Id"),
	x_session_id: Optional[str] = fastapi.Header(None, alias="X-Session-Id"),
) -> tuple[Optional[uuid.UUID], Optional[str]]:
	"""
	Validate cart identity headers.
	Returns (user_id, session_id) tuple.
	Raises HTTPException if validation fails.
	"""
	if not x_user_id and not x_session_id:
		raise fastapi.HTTPException(
			status_code=400,
			detail={
				"code": "MISSING_CART_IDENTITY",
				"message": "Передайте X-User-Id или X-Session-Id",
			},
		)

	if x_user_id and x_session_id:
		raise fastapi.HTTPException(
			status_code=400,
			detail={
				"code": "BOTH_IDENTITIES_PROVIDED",
				"message": "Передайте только один из заголовков: X-User-Id или X-Session-Id",
			},
		)

	user_id = None
	if x_user_id:
		try:
			user_id = uuid.UUID(x_user_id)
		except ValueError as e:
			raise fastapi.HTTPException(
				status_code=400,
				detail={
					"code": "INVALID_USER_ID",
					"message": "X-User-Id должен быть валидным UUID",
				},
			) from e

	return user_id, x_session_id


@router.get("", response_model=CartResponse)
async def get_cart(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	x_user_id: Annotated[Optional[str], fastapi.Header(alias="X-User-Id")] = None,
	x_session_id: Annotated[Optional[str], fastapi.Header(alias="X-Session-Id")] = None,
) -> CartResponse:
	"""Get cart contents with enriched product data

	Args:
		db (AsyncSession): database session
		x_user_id (Optional[str]): User ID from X-User-Id header
		x_session_id (Optional[str]): Session ID from X-Session-Id header

	Raises:
		fastapi.HTTPException(400): Missing or invalid cart identity
		fastapi.HTTPException(503): Service unavailable

	Returns:
		CartResponse: Cart contents with enriched product data
	"""
	try:
		user_id, session_id = validate_cart_identity(x_user_id, x_session_id)
		return await cart_service.get_cart(db, user_id, session_id)
	except fastapi.HTTPException:
		raise
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
