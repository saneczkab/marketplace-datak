import secrets
from typing import Callable

from core.config import settings
from fastapi import Request
from fastapi.responses import JSONResponse

SERVICE_KEY_PATH_PREFIXES = ("/api/v1/public", "/api/v1/inventory")


async def verify_service_key(request: Request, call_next: Callable) -> JSONResponse:
	if not any(
		request.url.path.startswith(prefix) for prefix in SERVICE_KEY_PATH_PREFIXES
	):
		return await call_next(request)

	service_key = request.headers.get("X-Service-Key")
	expected = settings.B2C_SERVICE_KEY
	if (
		not service_key
		or not expected
		or not secrets.compare_digest(service_key, expected)
	):
		return JSONResponse(
			status_code=401,
			content={
				"code": "UNAUTHORIZED",
				"message": "Invalid or missing service key",
			},
		)

	return await call_next(request)
