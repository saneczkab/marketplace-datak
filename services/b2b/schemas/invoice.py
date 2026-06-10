from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List
from database.models.catalog.inventory import InvoiceStatusEnum


class InvoiceItemCreate(BaseModel):
	sku_id: UUID
	quantity: int


class InvoiceAcceptItem(BaseModel):
	invoice_item_id: UUID
	accepted_quantity: int


class InvoiceItemResponse(BaseModel):
	id: UUID
	sku_id: UUID
	quantity: int
	accepted_quantity: int

	model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
	items: List[InvoiceItemCreate]


class InvoiceAccept(BaseModel):
	accepted_items: List[InvoiceAcceptItem]


class InvoiceResponse(BaseModel):
	id: UUID
	seller_id: UUID
	status: InvoiceStatusEnum
	items: List[InvoiceItemResponse]
	created_at: datetime
	updated_at: datetime
	accepted_at: datetime | None = None
	accepted_by: UUID | None = None

	model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
	items: List[InvoiceResponse]
	total_count: int
	limit: int
	offset: int
