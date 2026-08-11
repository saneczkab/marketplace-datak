import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SellerResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: uuid.UUID
	email: EmailStr
	first_name: str
	last_name: str
	middle_name: str | None
	company_name: str
	phone: str | None
	created_at: datetime
	updated_at: datetime


class SellerUpdate(BaseModel):
	email: EmailStr
	first_name: Annotated[str, Field(min_length=3, max_length=15)]
	last_name: Annotated[str, Field(min_length=3, max_length=15)]
	middle_name: Annotated[str, Field(min_length=3, max_length=15)] | None
	company_name: Annotated[str, Field(min_length=3, max_length=50)]
	phone: str
	password: str | None = None
