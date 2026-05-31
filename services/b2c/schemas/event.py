from enum import Enum
from datetime import datetime
import uuid

from pydantic import BaseModel


class EventTypeEnum(str, Enum):
	PRODUCT_BLOCKED = "PRODUCT_BLOCKED"
	PRODUCT_HARD_BLOCKED = "PRODUCT_HARD_BLOCKED"
	PRODUCT_DELETED = "PRODUCT_DELETED"
	SKU_OUT_OF_STOCK = "SKU_OUT_OF_STOCK"
	PRICE_CHANGED = "PRICE_CHANGED"


class EventProductRef(BaseModel):
	product_id: uuid.UUID
	reason: str


class EventSkuStock(BaseModel):
	sku_id: uuid.UUID
	product_id: uuid.UUID  # Why
	available_quantity: int


class EventPriceChanged(BaseModel):
	sku_id: uuid.UUID
	product_id: uuid.UUID
	old_price: int
	new_price: int


class B2BEvent(BaseModel):
	event_type: EventTypeEnum
	idempotency_key: uuid.UUID
	occured_at: datetime
	payload: EventProductRef | EventSkuStock | EventPriceChanged
