import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_CODE_PATTERN = re.compile(r"^[A-Z_]+$")


class BlockingReasonResponse(BaseModel):
	id: UUID
	code: str
	title: str
	description: str | None
	hard_block: bool
	is_active: bool


class BlockingReasonCreateRequest(BaseModel):
	code: str = Field(max_length=64)
	title: str = Field(max_length=200)
	description: str | None = Field(default=None, max_length=2000)
	hard_block: bool

	@field_validator("code")
	@classmethod
	def validate_code(cls, value: str) -> str:
		if not _CODE_PATTERN.match(value):
			raise ValueError("code must match ^[A-Z_]+$")
		return value


class BlockingReasonUpdateRequest(BaseModel):
	title: str | None = Field(default=None, max_length=200)
	description: str | None = Field(default=None, max_length=2000)
	is_active: bool | None = None
