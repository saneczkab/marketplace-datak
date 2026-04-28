from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional
from datetime import datetime


class CharacteristicSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    value: str

    model_config = ConfigDict(from_attributes=True)


class ImageSchema(BaseModel):
    id: Optional[UUID] = None
    url: str
    ordering: int = 0

    model_config = ConfigDict(from_attributes=True)


class SkuCreate(BaseModel):
    product_id: UUID
    name: str
    price: int
    active_quantity: int = 0
    characteristics: Optional[List[CharacteristicSchema]] = []
    images: Optional[List[ImageSchema]] = []


class SkuResponse(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    price: int
    active_quantity: int = Field(serialization_alias="activeQuantity")
    created_at: datetime
    updated_at: datetime
    
    characteristics: List[CharacteristicSchema] = []
    images: List[ImageSchema] = []

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

