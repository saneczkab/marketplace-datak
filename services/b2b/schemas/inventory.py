from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
	sku_id: UUID
	quantity: int = Field(gt=0)


class ReserveRequest(BaseModel):
	idempotency_key: UUID
	order_id: UUID
	items: list[InventoryItem] = Field(min_length=1)


class ReserveResponse(BaseModel):
	order_id: UUID
	status: str = "RESERVED"
	reserved_at: datetime


class InventoryOrderRequest(BaseModel):
	order_id: UUID
	items: list[InventoryItem] = Field(min_length=1)


class InventoryOrderResponse(BaseModel):
	order_id: UUID
	status: str
	processed_at: datetime
