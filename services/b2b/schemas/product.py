from typing import Optional

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from database.models.catalog.base import ProductStatusEnum

class ProductCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str | None = None
    category_id: UUID
    slug: str

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