from collections.abc import Callable

import crud.session as session_crud
from core.db import get_db
from core.security import decode_access_token
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError

PRIVATE_PATH_PREFIXES = ["/api/v1/tickets"]


async def _authenticate_bearer(request: Request) -> JSONResponse | None:
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
	except JWTError, ValueError:
		return JSONResponse(
			status_code=401,
			content={"code": "UNAUTHORIZED", "message": "Invalid or expired token"},
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
	if not any(request.url.path.startswith(prefix) for prefix in PRIVATE_PATH_PREFIXES):
		return await call_next(request)

	auth_error = await _authenticate_bearer(request)
	if auth_error is not None:
		return auth_error

	return await call_next(request)
