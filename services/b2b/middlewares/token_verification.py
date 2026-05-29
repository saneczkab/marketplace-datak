from typing import Callable
from fastapi import Request
from fastapi.responses import JSONResponse
from core.security import decode_access_token
from jose import JWTError
from core import db as core_db
import crud.session as session_crud

PRIVATE_PATHS = ["/api/v1/products"]


async def verify_token(request: Request, call_next: Callable) -> JSONResponse:
	if request.url.path not in PRIVATE_PATHS:
		return await call_next(request)

	auth_header = request.headers.get("Authorization")
	if not auth_header or not auth_header.startswith("Bearer "):
		return JSONResponse(
			status_code=401,
			content={"detail": "Missing or invalid Authorization header"},
		)

	token = auth_header.split(" ", 1)[1]

	try:
		decoded = decode_access_token(token)
		request.state.user_id = decoded.get("user_id")
	except JWTError:
		return JSONResponse(
			status_code=401, content={"detail": "Invalid or expired token"}
		)
	except ValueError as e:
		return JSONResponse(status_code=401, content={"detail": str(e)})
	get_db_dep = request.app.dependency_overrides.get(core_db.get_db, core_db.get_db)
	async for db in get_db_dep():
		try:
			is_active = await session_crud.check_active_session(token, db)
			if not is_active:
				return JSONResponse(
					status_code=401, content={"detail": "Token invalidated in db"}
				)
		finally:
			await db.close()
		break

	return await call_next(request)
