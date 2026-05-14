# middlewares/verify_token.py
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import Response
from core.security import decode_access_token
from core.db import get_db
from jose import JWTError
import crud.session as session_crud
from sqlalchemy.ext.asyncio import AsyncSession

PRIVATE_PATHS = ["/api/v1/auth/me", "/api/v1/auth/logout"]


async def verify_token(request: Request, call_next: Callable) -> Response:
	# 1. Если путь не в списке приватных → сразу пропускаем запрос
	if request.url.path not in PRIVATE_PATHS:
		return await call_next(request)

	auth_header = request.headers.get("Authorization")
	if not auth_header or not auth_header.startswith("Bearer "):
		raise HTTPException(
			status_code=401, detail="Missing or invalid Authorization header"
		)

	token = auth_header.split(" ", 1)[1]
	try:
		# decode_access_token — синхронная функция, await не нужен
		decoded = decode_access_token(token)
		request.state.user_id = decoded.get("user_id")
	except JWTError as e:
		raise HTTPException(status_code=401, detail="Invalid or expired token") from e
	except ValueError as e:
		raise HTTPException(status_code=401, detail=str(e)) from e

	db_gen = get_db()
	db: AsyncSession = await db_gen.__anext__()
	if not session_crud.check_active_session(token, db):
		raise HTTPException(status_code=401, detail="Token invalidated in db")

	response = await call_next(request)
	return response
