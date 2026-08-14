from uuid import UUID

from pydantic import BaseModel, EmailStr


class SellerInfoResponse(BaseModel):
	id: UUID
	first_name: str
	last_name: str
	middle_name: str

	company_name: str


class SellerInfoPatch(BaseModel):
	email: EmailStr
	phone: str
	first_name: str
	last_name: str
	middle_name: str
	company_name: str
