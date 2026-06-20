import uuid

import httpx

from core.config import settings
from exceptions.order import B2BUnavailableError, ReserveFailedError

RESERVE_PATH = "/api/v1/inventory/reserve"
UNRESERVE_PATH = "/api/v1/inventory/unreserve"


class B2BClient:
	def __init__(
		self,
		base_url: str | None = None,
		service_key: str | None = None,
		timeout: float | None = None,
	) -> None:
		self._base_url = (base_url or settings.B2B_BASE_URL).rstrip("/")
		self._service_key = service_key or settings.B2B_SERVICE_KEY
		self._timeout = timeout if timeout is not None else settings.B2B_REQUEST_TIMEOUT

	async def reserve(
		self,
		idempotency_key: uuid.UUID,
		order_id: uuid.UUID,
		items: list[dict],
	) -> None:
		payload = {
			"idempotency_key": str(idempotency_key),
			"order_id": str(order_id),
			"items": items,
		}
		headers = {"X-Service-Key": self._service_key}

		try:
			async with httpx.AsyncClient(
				base_url=self._base_url, timeout=self._timeout
			) as client:
				response = await client.post(
					RESERVE_PATH, json=payload, headers=headers
				)
		except (httpx.TimeoutException, httpx.TransportError) as err:
			raise B2BUnavailableError() from err

		if response.status_code == 200:
			return

		if response.status_code in (409, 404):
			raise ReserveFailedError(self._extract_failed_items(response, items))

		raise B2BUnavailableError()

	async def unreserve(
		self,
		order_id: uuid.UUID,
		items: list[dict],
	) -> None:
		payload = {
			"order_id": str(order_id),
			"items": items,
		}
		headers = {"X-Service-Key": self._service_key}

		try:
			async with httpx.AsyncClient(
				base_url=self._base_url, timeout=self._timeout
			) as client:
				response = await client.post(
					UNRESERVE_PATH, json=payload, headers=headers
				)
		except (httpx.TimeoutException, httpx.TransportError) as err:
			raise B2BUnavailableError() from err

		if response.status_code == 200:
			return

		raise B2BUnavailableError()

	@staticmethod
	def _extract_failed_items(
		response: httpx.Response, items: list[dict]
	) -> list[dict]:
		try:
			body = response.json()
		except ValueError:
			body = {}

		details = body.get("details") if isinstance(body, dict) else None
		if isinstance(details, dict):
			failed_items = details.get("failed_items")
			if isinstance(failed_items, list) and failed_items:
				return failed_items

		return [
			{
				"sku_id": item["sku_id"],
				"requested": item["quantity"],
				"reason": "SKU_NOT_FOUND",
			}
			for item in items
		]


_default_client = B2BClient()


def get_b2b_client() -> B2BClient:
	return _default_client
