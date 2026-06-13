from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class ModerationEventType(str, Enum):
	MODERATED = "MODERATED"
	BLOCKED = "BLOCKED"


class ModerationEventRequest(BaseModel):
	idempotency_key: UUID
	product_id: UUID
	event_type: ModerationEventType
	moderator_id: UUID | None = None
	moderator_comment: str | None = None
	occurred_at: datetime
