from enum import Enum
from datetime import datetime
import uuid
from typing import Union, Dict, Type

from pydantic import BaseModel


class EventTypeEnum(str, Enum):
	PRODUCT_BLOCKED = "PRODUCT_BLOCKED"
	PRODUCT_HARD_BLOCKED = "PRODUCT_HARD_BLOCKED"
	PRODUCT_DELETED = "PRODUCT_DELETED"
	SKU_OUT_OF_STOCK = "SKU_OUT_OF_STOCK"
	PRICE_CHANGED = "PRICE_CHANGED"
	SKU_BACK_IN_STOCK = "SKU_BACK_IN_STOCK"
	ORDER_FULFILLED = "ORDER_FULFILLED"
	ORDER_DELIVERED = "ORDER_DELIVERED"


class EventProductRef(BaseModel):
	product_id: uuid.UUID
	reason: str | None = None


class EventSkuStock(BaseModel):
	sku_id: uuid.UUID
	product_id: uuid.UUID
	available_quantity: int


class EventPriceChanged(BaseModel):
	sku_id: uuid.UUID
	product_id: uuid.UUID
	old_price: int
	new_price: int


class OrderFulfilledItem(BaseModel):
	sku_id: uuid.UUID
	quantity: int


class EventOrderFulfilled(BaseModel):
	order_id: uuid.UUID  # Also used as idempotency_key
	items: list[OrderFulfilledItem]


class EventOrderDelivered(BaseModel):
	order_id: uuid.UUID
	buyer_id: uuid.UUID


EventPayload = Union[
	EventProductRef,
	EventSkuStock,
	EventPriceChanged,
	EventOrderFulfilled,
	EventOrderDelivered,
]


class Event(BaseModel):
	event_type: EventTypeEnum
	idempotency_key: uuid.UUID
	occurred_at: datetime
	payload: EventPayload


EVENT_TYPE_TO_PAYLOAD_CLASS: Dict[EventTypeEnum, Type[BaseModel]] = {
	EventTypeEnum.PRODUCT_BLOCKED: EventProductRef,
	EventTypeEnum.PRODUCT_HARD_BLOCKED: EventProductRef,
	EventTypeEnum.PRODUCT_DELETED: EventProductRef,
	EventTypeEnum.SKU_OUT_OF_STOCK: EventSkuStock,
	EventTypeEnum.PRICE_CHANGED: EventPriceChanged,
	EventTypeEnum.SKU_BACK_IN_STOCK: EventSkuStock,
	EventTypeEnum.ORDER_FULFILLED: EventOrderFulfilled,
	EventTypeEnum.ORDER_DELIVERED: EventOrderDelivered,
}


def dict_to_payload(event_type: EventTypeEnum, data: dict) -> EventPayload:
	"""
	Turn dict into payload.
	"""
	payload_class = EVENT_TYPE_TO_PAYLOAD_CLASS.get(event_type)
	if not payload_class:
		raise ValueError(f"Неподдерживаемый тип события: {event_type}")

	return payload_class.model_validate(data)
