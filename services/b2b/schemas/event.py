import uuid
from enum import Enum
from pydantic import BaseModel


class EventTypeEnum(str, Enum):
	ORDER_FULFILLED = "ORDER_FULFILLED"


class EventOrderFulfilled(BaseModel):
	oreder_id: uuid.UUID
