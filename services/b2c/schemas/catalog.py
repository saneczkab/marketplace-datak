import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryRef(BaseModel):
	id: uuid.UUID
	name: str
	parent_id: uuid.UUID | None = None
	level: int = Field(ge=0)
	path: List[str]
	model_config = ConfigDict(from_attributes=True)


class ImageRef(BaseModel):
	id: uuid.UUID
	url: str
	alt: str = ""
	ordering: int = Field(ge=0)
	is_main: bool = False
	model_config = ConfigDict(from_attributes=True)


class CatalogProductSeller(BaseModel):
	id: uuid.UUID
	display_name: str
	model_config = ConfigDict(from_attributes=True)


class CatalogProductCard(BaseModel):
	id: uuid.UUID
	name: str
	slug: str
	category: CategoryRef
	min_price: int
	old_price: Optional[int] = None
	has_stock: bool
	rating: Optional[float] = Field(default=None, ge=0, le=5)
	reviews_count: int = Field(ge=0)
	images: List[ImageRef]
	seller: CatalogProductSeller
	model_config = ConfigDict(from_attributes=True)


class PaginatedCatalogProducts(BaseModel):
	items: List[CatalogProductCard]
	total_count: int
	limit: int
	offset: int
	model_config = ConfigDict(from_attributes=True)
