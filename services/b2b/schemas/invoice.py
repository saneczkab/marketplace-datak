from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List
from database.models.catalog.inventory import InvoiceStatusEnum


class InvoiceItemCreate(BaseModel):
	sku_id: UUID
	quantity: int


class InvoiceItemResponse(BaseModel):
	sku_id: UUID
	sku_name: str
	quantity: int
	accepted_quantity: int | None = None

	model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
	items: List[InvoiceItemCreate]


class InvoiceResponse(BaseModel):
	id: UUID
	seller_id: UUID
	status: InvoiceStatusEnum
	items: List[InvoiceItemResponse]
	created_at: datetime
	accepted_at: datetime | None = None
	updated_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
	total: int
	items: List[InvoiceResponse]
	limit: int
	offset: int
