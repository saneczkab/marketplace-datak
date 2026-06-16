from typing import Callable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from core.config import settings

SERVICE_API_PATHS = ["/api/v1/b2b/events"]


def _validate_service_key(request: Request) -> Optional[JSONResponse]:
	if request.headers.get("X-Service-key") != settings.X_SERVICE_KEY:
		return JSONResponse(
			status_code=401,
			content={
				"code": "Invalid-X-Service-key",
				"message": f"X-Service-key is invalid: '{request.headers.get('X-Service-key')}' != '{settings.X_SERVICE_KEY}'",
			},
		)


async def service_key_verification(
	request: Request, call_next: Callable
) -> JSONResponse:
	if request.url.path not in SERVICE_API_PATHS:
		return await call_next(request)

	validation_error = _validate_service_key(request)

	if validation_error:
		return validation_error

	return await call_next(request)
