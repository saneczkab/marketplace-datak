from enum import Enum
from datetime import datetime
import uuid
from typing import Annotated, Literal, Union, Dict, Type

from pydantic import BaseModel, Field


class EventTypeEnum(str, Enum):
	PRODUCT_BLOCKED = "PRODUCT_BLOCKED"
	PRODUCT_HARD_BLOCKED = "PRODUCT_HARD_BLOCKED"
	PRODUCT_DELETED = "PRODUCT_DELETED"
	SKU_OUT_OF_STOCK = "SKU_OUT_OF_STOCK"
	PRICE_CHANGED = "PRICE_CHANGED"
	BACK_IN_STOCK = "BACK_IN_STOCK"
	ORDER_FULFILLED = "ORDER_FULFILLED"


class BaseEventPayload(BaseModel):
	type: str


class EventProductRef(BaseEventPayload):
	type: Literal["product_ref"] = "product_ref"
	product_id: uuid.UUID
	reason: str


class EventSkuStock(BaseEventPayload):
	type: Literal["sku_stock"] = "sku_stock"
	sku_id: uuid.UUID
	product_id: uuid.UUID  # Why
	available_quantity: int


class EventPriceChanged(BaseEventPayload):
	type: Literal["price_changed"] = "price_changed"
	sku_id: uuid.UUID
	product_id: uuid.UUID
	old_price: int
	new_price: int


class OrderFulfilledItem(BaseModel):
	sku_id: uuid.UUID
	quantity: int


class EventOrderFulfilled(BaseEventPayload):
	type: Literal["order_fulfilled"] = "order_fulfilled"
	order_id: uuid.UUID  # Also used as idempotency_key
	items: list[OrderFulfilledItem]


EventPayload = Annotated[
	Union[EventProductRef, EventSkuStock, EventPriceChanged, EventOrderFulfilled],
	Field(discriminator="type"),
]


class Event(BaseModel):
	event_type: EventTypeEnum
	idempotency_key: uuid.UUID
	occured_at: datetime
	payload: EventPayload


EVENT_TYPE_TO_PAYLOAD_CLASS: Dict[EventTypeEnum, Type[BaseEventPayload]] = {
	EventTypeEnum.PRODUCT_BLOCKED: EventProductRef,
	EventTypeEnum.PRODUCT_HARD_BLOCKED: EventProductRef,
	EventTypeEnum.PRODUCT_DELETED: EventProductRef,
	EventTypeEnum.SKU_OUT_OF_STOCK: EventSkuStock,
	EventTypeEnum.PRICE_CHANGED: EventPriceChanged,
	EventTypeEnum.BACK_IN_STOCK: EventSkuStock,
	EventTypeEnum.ORDER_FULFILLED: EventOrderFulfilled,
}


def dict_to_payload(event_type: EventTypeEnum, data: dict) -> EventPayload:
	"""
	Turn dict into payload. Probably doesn't belong here
	"""
	if event_type not in EVENT_TYPE_TO_PAYLOAD_CLASS:
		raise ValueError(f"Неподдерживаемый тип события: {event_type}")

	payload_class = EVENT_TYPE_TO_PAYLOAD_CLASS[event_type]
	return payload_class(**data)
