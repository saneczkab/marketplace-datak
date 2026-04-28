import uuid
from typing import Annotated, Optional

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from core import db
from exceptions.cart import CartItemNotFoundError
from exceptions.sku import SkuNotFoundError
from schemas.cart import (
	AddCartItemRequest,
	CartItem,
	CartMutationResponse,
	CartResponse,
	CartValidationResponse,
	UpdateCartItemRequest,
)
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


@router.delete("", status_code=204)
async def clear_cart(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	x_user_id: Annotated[Optional[str], fastapi.Header(alias="X-User-Id")] = None,
	x_session_id: Annotated[Optional[str], fastapi.Header(alias="X-Session-Id")] = None,
) -> None:
	"""Clear all items from cart

	Args:
		db (AsyncSession): database session
		x_user_id (Optional[str]): User ID from X-User-Id header
		x_session_id (Optional[str]): Session ID from X-Session-Id header

	Raises:
		fastapi.HTTPException(400): Missing or invalid cart identity
		fastapi.HTTPException(500): Internal server error
	"""
	try:
		user_id, session_id = validate_cart_identity(x_user_id, x_session_id)
		await cart_service.cart_crud.clear_cart(db, user_id, session_id)
	except fastapi.HTTPException:
		raise
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e


@router.post("/items", response_model=CartMutationResponse, status_code=201)
async def add_cart_item(
	request: AddCartItemRequest,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	x_user_id: Annotated[Optional[str], fastapi.Header(alias="X-User-Id")] = None,
	x_session_id: Annotated[Optional[str], fastapi.Header(alias="X-Session-Id")] = None,
) -> CartMutationResponse:
	"""Add item to cart

	Args:
		request (AddCartItemRequest): SKU ID and quantity
		db (AsyncSession): database session
		x_user_id (Optional[str]): User ID from X-User-Id header
		x_session_id (Optional[str]): Session ID from X-Session-Id header

	Raises:
		fastapi.HTTPException(400): Invalid request
		fastapi.HTTPException(404): SKU not found
		fastapi.HTTPException(410): SKU not available
		fastapi.HTTPException(422): Insufficient stock
		fastapi.HTTPException(503): Service unavailable

	Returns:
		CartMutationResponse: Updated cart item and summary
	"""
	try:
		user_id, session_id = validate_cart_identity(x_user_id, x_session_id)
		return await cart_service.add_cart_item(
			db, user_id, session_id, request.sku_id, request.quantity
		)
	except fastapi.HTTPException:
		raise
	except SkuNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except ValueError as e:
		error_msg = str(e)
		if "SKU_NOT_AVAILABLE" in error_msg:
			raise fastapi.HTTPException(status_code=410, detail=error_msg) from e
		if "INSUFFICIENT_STOCK" in error_msg:
			raise fastapi.HTTPException(status_code=422, detail=error_msg) from e
		raise fastapi.HTTPException(status_code=400, detail=error_msg) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.get("/items/{item_id}", response_model=CartItem)
async def get_cart_item(
	item_id: uuid.UUID,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	x_user_id: Annotated[Optional[str], fastapi.Header(alias="X-User-Id")] = None,
	x_session_id: Annotated[Optional[str], fastapi.Header(alias="X-Session-Id")] = None,
) -> CartItem:
	"""Get single cart item

	Args:
		item_id (uuid.UUID): Cart item ID
		db (AsyncSession): database session
		x_user_id (Optional[str]): User ID from X-User-Id header
		x_session_id (Optional[str]): Session ID from X-Session-Id header

	Raises:
		fastapi.HTTPException(400): Missing or invalid cart identity
		fastapi.HTTPException(404): Cart item not found
		fastapi.HTTPException(503): Service unavailable

	Returns:
		CartItem: Enriched cart item
	"""
	try:
		user_id, session_id = validate_cart_identity(x_user_id, x_session_id)
		return await cart_service.get_cart_item(db, user_id, session_id, item_id)
	except fastapi.HTTPException:
		raise
	except CartItemNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.put("/items/{item_id}", response_model=CartMutationResponse)
async def update_cart_item(
	item_id: uuid.UUID,
	request: UpdateCartItemRequest,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	x_user_id: Annotated[Optional[str], fastapi.Header(alias="X-User-Id")] = None,
	x_session_id: Annotated[Optional[str], fastapi.Header(alias="X-Session-Id")] = None,
) -> CartMutationResponse:
	"""Update cart item quantity

	Args:
		item_id (uuid.UUID): Cart item ID
		request (UpdateCartItemRequest): New quantity
		db (AsyncSession): database session
		x_user_id (Optional[str]): User ID from X-User-Id header
		x_session_id (Optional[str]): Session ID from X-Session-Id header

	Raises:
		fastapi.HTTPException(400): Invalid request
		fastapi.HTTPException(403): Access denied
		fastapi.HTTPException(404): Cart item not found
		fastapi.HTTPException(410): Product not available
		fastapi.HTTPException(422): Insufficient stock
		fastapi.HTTPException(503): Service unavailable

	Returns:
		CartMutationResponse: Updated cart item and summary
	"""
	try:
		user_id, session_id = validate_cart_identity(x_user_id, x_session_id)
		return await cart_service.update_cart_item(
			db, user_id, session_id, item_id, request.quantity
		)
	except fastapi.HTTPException:
		raise
	except CartItemNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except PermissionError as e:
		raise fastapi.HTTPException(status_code=403, detail=str(e)) from e
	except ValueError as e:
		error_msg = str(e)
		if "PRODUCT_NOT_AVAILABLE" in error_msg:
			raise fastapi.HTTPException(status_code=410, detail=error_msg) from e
		if "INSUFFICIENT_STOCK" in error_msg:
			raise fastapi.HTTPException(status_code=422, detail=error_msg) from e
		raise fastapi.HTTPException(status_code=400, detail=error_msg) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e


@router.delete("/items/{item_id}", status_code=204)
async def delete_cart_item(
	item_id: uuid.UUID,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	x_user_id: Annotated[Optional[str], fastapi.Header(alias="X-User-Id")] = None,
	x_session_id: Annotated[Optional[str], fastapi.Header(alias="X-Session-Id")] = None,
) -> None:
	"""Delete cart item

	Args:
		item_id (uuid.UUID): Cart item ID
		db (AsyncSession): database session
		x_user_id (Optional[str]): User ID from X-User-Id header
		x_session_id (Optional[str]): Session ID from X-Session-Id header

	Raises:
		fastapi.HTTPException(400): Missing or invalid cart identity
		fastapi.HTTPException(404): Cart item not found
		fastapi.HTTPException(500): Internal server error
	"""
	try:
		user_id, session_id = validate_cart_identity(x_user_id, x_session_id)
		await cart_service.delete_cart_item(db, user_id, session_id, item_id)
	except fastapi.HTTPException:
		raise
	except CartItemNotFoundError as e:
		raise fastapi.HTTPException(status_code=404, detail=str(e)) from e
	except Exception as e:
		raise fastapi.HTTPException(status_code=500, detail=str(e)) from e


# Validation endpoint with JWT stub
validate_router = fastapi.APIRouter(prefix="/cart", tags=["Корзина"])


@validate_router.get("/validate", response_model=CartValidationResponse)
async def validate_cart(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	authorization: Annotated[Optional[str], fastapi.Header()] = None,
	cart_item_ids: Annotated[Optional[list[str]], fastapi.Query()] = None,
) -> CartValidationResponse:
	"""Validate cart items (JWT stub)

	Args:
		db (AsyncSession): database session
		authorization (Optional[str]): Bearer token (stub for now)
		cart_item_ids (Optional[list[str]]): Specific items to validate

	Raises:
		fastapi.HTTPException(401): Unauthorized
		fastapi.HTTPException(503): Service unavailable

	Returns:
		CartValidationResponse: Validation results
	"""
	# JWT stub - extract user_id from token (placeholder)
	if not authorization or not authorization.startswith("Bearer "):
		raise fastapi.HTTPException(
			status_code=401,
			detail={"code": "UNAUTHORIZED", "message": "Требуется авторизация"},
		)

	# Replace with actual JWT parsing when auth is implemented
	# For now, just use a placeholder user_id
	user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

	try:
		return await cart_service.validate_cart(db, user_id, cart_item_ids)
	except Exception as e:
		raise fastapi.HTTPException(status_code=503, detail=str(e)) from e
