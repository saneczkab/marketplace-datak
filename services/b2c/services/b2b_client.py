import httpx
from typing import Dict, Any, Optional
from core.config import settings
from exceptions.b2b_client import B2BServiceUnavailableError, B2BNotFoundError


B2B_URL = getattr(settings, "B2B_SERVICE_URL", "http://localhost:8001")
B2B_KEY = getattr(settings, "B2B_SERVICE_KEY", "b2b_secret_service_key_placeholder")


async def request_b2b(
	method: str, endpoint: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
	"""Basic method for sending authorized requests to a B2B service"""
	url = f"{B2B_URL.rstrip('/')}{endpoint}"
	headers = {"X-Service-Key": B2B_KEY}

	try:
		async with httpx.AsyncClient(timeout=5.0) as client:
			response = await client.request(method, url, params=params, headers=headers)

			if response.status_code == 404:
				raise B2BNotFoundError("Resource not found in B2B service")

			if response.status_code >= 500:
				raise B2BServiceUnavailableError(f"B2B service error: {response.text}")

			response.raise_for_status()
			return response.json()

	except (httpx.RequestError, httpx.HTTPStatusError) as e:
		if isinstance(e, B2BNotFoundError):
			raise e
		raise B2BServiceUnavailableError(
			"B2B service is temporarily unavailable"
		) from e
