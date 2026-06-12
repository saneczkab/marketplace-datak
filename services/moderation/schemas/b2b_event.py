from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from schemas.product_snapshot import ProductSnapshot


class B2BEventType(str, Enum):
	PRODUCT_CREATED = "PRODUCT_CREATED"
	PRODUCT_EDITED = "PRODUCT_EDITED"
	PRODUCT_DELETED = "PRODUCT_DELETED"


class EventProductCreatedPayload(BaseModel):
	product_id: UUID
	seller_id: UUID
	category_id: UUID | None = None
	queue_priority: int = Field(default=3, ge=1, le=4)
	json_after: ProductSnapshot


class EventProductEditedPayload(BaseModel):
	product_id: UUID
	seller_id: UUID
	category_id: UUID | None = None
	queue_priority: int = Field(default=3, ge=1, le=4)
	json_before: ProductSnapshot
	json_after: ProductSnapshot


class EventProductDeletedPayload(BaseModel):
	product_id: UUID


class IncomingB2BEvent(BaseModel):
	event_type: B2BEventType
	idempotency_key: UUID
	occurred_at: datetime
	payload: (
		EventProductCreatedPayload
		| EventProductEditedPayload
		| EventProductDeletedPayload
	)

	@model_validator(mode="before")
	@classmethod
	def parse_payload(cls, data: Any) -> Any:  # noqa: ANN401
		if not isinstance(data, dict):
			return data
		raw_payload = data.get("payload")
		if raw_payload is None or not isinstance(raw_payload, dict):
			return data
		event_type = data.get("event_type")
		if event_type in (B2BEventType.PRODUCT_CREATED, "PRODUCT_CREATED"):
			data["payload"] = EventProductCreatedPayload.model_validate(raw_payload)
		elif event_type in (B2BEventType.PRODUCT_EDITED, "PRODUCT_EDITED"):
			data["payload"] = EventProductEditedPayload.model_validate(raw_payload)
		else:
			data["payload"] = EventProductDeletedPayload.model_validate(raw_payload)
		return data
