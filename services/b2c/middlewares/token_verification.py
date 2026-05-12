from typing import Callable

from fastapi import FastAPI, Request, HTTPException

from core.security import decode_access_token

from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

app = FastAPI()

PRIVATE_PATHS = "something"


@app.middleware("http")
async def verify_token(request: Request, call_next: Callable) -> None:
	if request.url.path not in PRIVATE_PATHS:
		return await call_next(request)

	auth_header = request.headers.get("Authorization")

	if not auth_header or not auth_header.startswith("Bearer "):
		raise HTTPException(
			status_code=401, detail="Missing or invalid Authorization header"
		)

	token = auth_header.split(" ", 1)[1]
	try:
		decoded = await decode_access_token(token)
		request.state.user_id = decoded.get("user_id")

	except ExpiredSignatureError as e:
		raise HTTPException(status_code=401, detail="Expired token") from e

	except InvalidTokenError as e:
		raise HTTPException(status_code=401, detail="Invalid token") from e

	response = await call_next(request)
	return response
