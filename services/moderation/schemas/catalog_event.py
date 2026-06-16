from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class CatalogEventType(str, Enum):
	PRODUCT_UPDATE = "PRODUCT_UPDATE"
	SKU_UPDATE = "SKU_UPDATE"


class CategoryPayload(BaseModel):
	id: UUID
	name: str


class ImagePayload(BaseModel):
	id: UUID | None = None
	url: str
	ordering: int = 0


class CharacteristicPayload(BaseModel):
	id: UUID | None = None
	name: str
	value: str


class SkuPayload(BaseModel):
	id: UUID
	product_id: UUID
	name: str
	price: int = Field(ge=0)
	discount: int = Field(default=0, ge=0)
	active_quantity: int = Field(default=0, ge=0)
	article: str | None = None
	images: list[ImagePayload] = Field(default_factory=list)
	characteristics: list[CharacteristicPayload] = Field(default_factory=list)


class ProductUpdatePayload(BaseModel):
	id: UUID
	seller_id: UUID
	category_id: UUID
	category: CategoryPayload | None = None
	title: str
	slug: str
	description: str | None = None
	status: str
	deleted: bool = False
	images: list[ImagePayload] = Field(default_factory=list)
	characteristics: list[CharacteristicPayload] = Field(default_factory=list)
	skus: list[SkuPayload] = Field(default_factory=list)


class SkuUpdatePayload(BaseModel):
	id: UUID
	product_id: UUID
	name: str
	price: int = Field(ge=0)
	discount: int = Field(default=0, ge=0)
	active_quantity: int = Field(default=0, ge=0)
	article: str | None = None
	images: list[ImagePayload] = Field(default_factory=list)
	characteristics: list[CharacteristicPayload] = Field(default_factory=list)


class IncomingCatalogEvent(BaseModel):
	event_type: CatalogEventType
	idempotency_key: UUID
	occurred_at: datetime
	payload: ProductUpdatePayload | SkuUpdatePayload

	@model_validator(mode="before")
	@classmethod
	def parse_payload(cls, data: Any) -> Any:  # noqa: ANN401
		if not isinstance(data, dict):
			return data
		raw_payload = data.get("payload")
		if raw_payload is None or not isinstance(raw_payload, dict):
			return data
		event_type = data.get("event_type")
		if event_type in (CatalogEventType.PRODUCT_UPDATE, "PRODUCT_UPDATE"):
			data["payload"] = ProductUpdatePayload.model_validate(raw_payload)
		else:
			data["payload"] = SkuUpdatePayload.model_validate(raw_payload)
		return data
