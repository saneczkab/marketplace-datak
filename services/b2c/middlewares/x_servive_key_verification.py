from typing import Callable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from core.config import settings

SERVICE_API_PATHS = ["/api/v1/b2b/events"]


def _validate_service_key(request: Request) -> Optional[JSONResponse]:
	if request.headers.get("X-Serivce-key") != settings.X_Service_Key:
		return JSONResponse(
			status_code=401,
			content={
				"code": "Invalid_X_Service_key",
				"message": "X-Service-key is invalid",
			},
		)


async def service_key_verification(
	request: Request, call_next: Callable
) -> JSONResponse:
	if request.url.path not in SERVICE_API_PATHS:
		return await call_next(request)

	_validate_service_key(request)

	return await call_next(request)