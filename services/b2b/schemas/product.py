from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from database.models import ProductStatusEnum
from schemas.sku import SkuResponse


class Characteristic(BaseModel):
	name: str
	value: str


class ProductImageCreate(BaseModel):
	url: str
	ordering: int = 0


class ProductCreate(BaseModel):
	title: str = Field(..., min_length=1, max_length=255)
	description: str = Field(..., min_length=1, max_length=5000)
	category_id: UUID
	slug: Optional[str] = None
	images: List[ProductImageCreate] = []
	characteristics: List[Characteristic] = []


class ProductUpdate(BaseModel):
	title: Optional[str] = Field(None, min_length=1, max_length=255)
	description: Optional[str] = Field(None, max_length=5000)
	category_id: Optional[UUID] = None
	characteristics: Optional[List[Characteristic]] = None


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
	id: UUID
	url: str
	ordering: int


class CharacteristicsResponse(BaseModel):
	id: UUID
	name: str
	value: str
