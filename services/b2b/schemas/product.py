from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from database.models import ProductStatusEnum
from schemas.sku import SkuResponse


class ProductCreate(BaseModel):
	title: str = Field(..., min_length=5, max_length=255)
	description: str | None = None
	category_id: UUID
	slug: Optional[str]
	images: Optional[List[ProductImageCreate]]
	characteristics: Optional[List[Characteristic]]


class ProductUpdate(BaseModel):
	title: Optional[str] = Field(None, min_length=5, max_length=255)
	description: Optional[str] = None
	category_id: Optional[UUID] = None
	slug: Optional[str] = None
	status: Optional[ProductStatusEnum] = None


class ProductSellerRead(BaseModel):
	id: UUID
	title: str
	slug: str
	description: str | None
	status: ProductStatusEnum
	category_id: UUID
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class Characteristic(BaseModel):
	name: str
	value: str


class ProductImageCreate(BaseModel):
	url: str
	ordering: int


class ProductResponse(BaseModel):
	id: UUID
	seller_id: UUID
	category_id: UUID
	title: str
	slug: str
	description: str
	status: ProductStatusEnum
	deleted: bool
	blocking_reason_id: UUID | None
	moderator_comment: str | None
	images: List[ProductImageResponse]
	characteristics: List[CharacteristicsResponse]
	skus: List[SkuResponse]
	created_at: datetime
	updated_at: datetime


class ProductImageResponse(BaseModel):
	url: str
	ordering: int


class CharacteristicsResponse(BaseModel):
	name: str
	value: str
	id: UUID
