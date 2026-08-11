import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from jwt import JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from core.security import decode_access_token

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {
	"/docs",
	"/openapi.json",
	"/api/v1/health",
	"/api/v1/auth/login",
	"/api/v1/auth/register",
	"/metrics",
}
SELLERS_PATH_PREFIX = "/api/v1/sellers/"


class VerifyTokenMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next):
		path = request.url.path.rstrip("/") or "/"
		is_public_seller_read = (
			request.method == "GET" and path.startswith(SELLERS_PATH_PREFIX)
		)

		if path in PUBLIC_PATHS or is_public_seller_read:
			return await call_next(request)

		try:
			auth_header = request.headers.get("Authorization")
			if not auth_header or not auth_header.startswith("Bearer "):
				raise ValueError("Missing or invalid authorization header")

			token = auth_header.split(" ")[1]
			payload = decode_access_token(token)
			if payload is None:
				raise ValueError("Invalid token")

			request.state.user_id = payload.get("sub")
			return await call_next(request)
		except (JWTError, ValueError) as e:
			logger.warning(f"Authentication failed: {str(e)}")
			return JSONResponse(
				status_code=status.HTTP_401_UNAUTHORIZED,
				content={"detail": "Invalid or expired token"},
				headers={"WWW-Authenticate": "Bearer"},
			)
