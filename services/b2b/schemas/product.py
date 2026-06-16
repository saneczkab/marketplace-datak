import enum
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
	slug: str = Field(..., min_length=1, max_length=255)
	images: List[ProductImageCreate] = []
	characteristics: List[Characteristic] = []


class ProductUpdate(BaseModel):
	title: Optional[str] = Field(None, min_length=1, max_length=255)
	description: Optional[str] = Field(None, max_length=5000)
	category_id: Optional[UUID] = None
	characteristics: Optional[List[Characteristic]] = None


class ProductSellerListItem(BaseModel):
	id: UUID
	title: str
	slug: str
	status: ProductStatusEnum
	category_id: UUID
	deleted: bool
	created_at: datetime
	min_price: int | None = None
	cover_image: str | None = None
	skus_count: int
	total_active_quantity: int


class ProductSellerListResponse(BaseModel):
	items: List[ProductSellerListItem]
	total_count: int
	limit: int
	offset: int


class SellerProductStatusFilter(str, enum.Enum):
	CREATED = "CREATED"
	ON_MODERATION = "ON_MODERATION"
	MODERATED = "MODERATED"
	BLOCKED = "BLOCKED"
	HARD_BLOCKED = "HARD_BLOCKED"


class ProductImageResponse(BaseModel):
	id: UUID
	url: str
	ordering: int


class CharacteristicsResponse(BaseModel):
	id: UUID
	name: str
	value: str


class BlockingReason(BaseModel):
	id: UUID
	title: str
	comment: str


class FieldReport(BaseModel):
	field_name: str
	sku_id: UUID | None = None
	comment: str


class ProductDetailResponse(BaseModel):
	id: UUID
	seller_id: UUID
	category_id: UUID
	title: str
	slug: str
	description: str
	status: ProductStatusEnum
	deleted: bool
	images: List[ProductImageResponse]
	characteristics: List[CharacteristicsResponse]
	skus: List[SkuResponse]
	created_at: datetime
	updated_at: datetime
	blocked: bool
	blocking_reason: BlockingReason | None
	field_reports: List[FieldReport]


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
