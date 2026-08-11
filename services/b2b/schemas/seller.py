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
	phone: str
	created_at: datetime
	updated_at: datetime


class SellerUpdate(BaseModel):
	email: EmailStr | None = None
	password: Annotated[str, Field(min_length=8)] | None = None
	first_name: Annotated[str, Field(min_length=3, max_length=15)] | None = None
	last_name: Annotated[str, Field(min_length=3, max_length=15)] | None = None
	middle_name: Annotated[str, Field(min_length=3, max_length=15)] | None = None
	company_name: Annotated[str, Field(min_length=3, max_length=50)] | None = None
	phone: str | None = None
