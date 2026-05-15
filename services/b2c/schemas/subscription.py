import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

from schemas.collection import ProductSchema


class SubscribeRequest(BaseModel):
	"""Тело запроса для создания подписки"""

	notify_on: List[str] = Field(
		description="Список событий: IN_STOCK, PRICE_DOWN",
		min_length=1,
		example=["IN_STOCK", "PRICE_DOWN"],
	)


class SubscriptionResponse(BaseModel):
	"""Ответ с данными о подписке и товаре"""

	id: uuid.UUID
	product: ProductSchema
	notify_on: List[str]
	created_at: datetime
