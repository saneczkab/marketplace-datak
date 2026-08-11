from typing import Callable, Optional

import crud.session as session_crud
from core.db import get_db
from core.security import decode_access_token
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError

PRIVATE_PATHS: list[str] = []
PRIVATE_PATHS_PREFIXES = ["/api/v1/products", "/api/v1/skus", "/api/v1/invoices"]
SELLERS_PATH_PREFIX = "/api/v1/sellers/"


async def _authenticate_bearer(request: Request) -> Optional[JSONResponse]:
	auth_header = request.headers.get("Authorization")
	if not auth_header or not auth_header.startswith("Bearer "):
		return JSONResponse(
			status_code=401,
			content={
				"code": "UNAUTHORIZED",
				"message": "Missing or invalid Authorization header",
			},
		)

	token = auth_header.split(" ", 1)[1]
	try:
		decoded = decode_access_token(token)
		request.state.user_id = decoded.get("user_id")
		request.state.seller_id = decoded.get("seller_id")
	except JWTError:
		return JSONResponse(
			status_code=401,
			content={"code": "UNAUTHORIZED", "message": "Invalid or expired token"},
		)
	except ValueError as err:
		return JSONResponse(
			status_code=401, content={"code": "UNAUTHORIZED", "message": str(err)}
		)
	get_db_dep = request.app.dependency_overrides.get(get_db, get_db)
	async for db in get_db_dep():
		is_active = await session_crud.check_active_session(token, db)
		if not is_active:
			return JSONResponse(
				status_code=401,
				content={"code": "UNAUTHORIZED", "message": "Token invalidated in db"},
			)
		break

	return None


async def verify_token(request: Request, call_next: Callable) -> JSONResponse:
	is_private_seller_update = request.method == "PATCH" and request.url.path.startswith(
		SELLERS_PATH_PREFIX
	)
	is_private_path = request.url.path in PRIVATE_PATHS or any(
		request.url.path.startswith(prefix) for prefix in PRIVATE_PATHS_PREFIXES
	)
	if not is_private_path and not is_private_seller_update:
		return await call_next(request)

	auth_error = await _authenticate_bearer(request)
	if auth_error is not None:
		return auth_error

	return await call_next(request)
