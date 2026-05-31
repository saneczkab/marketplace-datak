from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from core.config import settings

SERVICE_API_PATHS = ["/api/v1/b2b/events"]

def

async def service_key_verification(
	request: Request, call_next: Callable
) -> JSONResponse:
	if request.url.path not in SERVICE_API_PATHS:
		return await call_next(request)

