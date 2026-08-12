from uuid import UUID

from pydantic import BaseModel


class SellerInfoResponse(BaseModel):
	id: UUID
	first_name: str
	last_name: str
	middle_name: str

	company_name: str
