from pydantic import BaseModel, Field
from uuid import UUID


class SkuCreate(BaseModel):
    product_id: UUID
    name: str
    price: int
    active_quantity: int


class SkuResponse(BaseModel):
    id: UUID
    name: str
    price: int
    activeQuantity: int = Field(alias="active_quantity")

    class Config:
        from_attributes = True
        populate_by_name = True
