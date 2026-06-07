from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, model_validator

from schemas.product import FieldReport


class ModerationEventType(str, Enum):
	MODERATED = "MODERATED"
	BLOCKED = "BLOCKED"


class ModerationEventRequest(BaseModel):
	idempotency_key: UUID
	product_id: UUID
	event_type: ModerationEventType
	moderator_id: UUID | None = None
	moderator_comment: str | None = None
	blocking_reason_id: UUID | None = None
	hard_block: bool = False
	field_reports: list[FieldReport] | None = None
	occurred_at: datetime

	@model_validator(mode="after")
	def validate_blocked_fields(self) -> "ModerationEventRequest":
		if (
			self.event_type == ModerationEventType.BLOCKED
			and self.blocking_reason_id is None
		):
			raise ValueError(
				"blocking_reason_id is required when event_type is BLOCKED"
			)
		return self
