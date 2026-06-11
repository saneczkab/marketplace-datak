import uuid
from typing import Any, List
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CategoryRef(BaseModel):
	id: uuid.UUID
	name: str
	parent_id: uuid.UUID | None = None
	level: int = Field(ge=0)
	path: List[str]
	model_config = ConfigDict(from_attributes=True)


class CategoryTreeNode(CategoryRef):
	children: List["CategoryTreeNode"] = Field(default_factory=list)
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
	min_price: int
	old_price: int | None = None
	slug: str | None = None
	category: CategoryRef | None = None
	has_stock: bool
	rating: float | None = Field(default=None, ge=0, le=5)
	reviews_count: int = Field(default=0, ge=0)
	images: List[ImageRef]
	seller: CatalogProductSeller | None = None
	model_config = ConfigDict(from_attributes=True)


class CatalogSku(BaseModel):
	id: uuid.UUID
	name: str | None = None
	sku_code: str | None = None
	price: int
	old_price: int | None = None
	available_quantity: int = Field(ge=0)
	attributes: dict[str, Any] = Field(default_factory=dict)
	images: List[ImageRef] = Field(default_factory=list)
	model_config = ConfigDict(from_attributes=True)


class CatalogProductDetail(CatalogProductCard):
	description: str
	attributes: dict[str, Any] = Field(default_factory=dict)
	skus: List[CatalogSku]
	model_config = ConfigDict(from_attributes=True)


class PaginatedCatalogProducts(BaseModel):
	items: List[CatalogProductCard]
	total_count: int
	limit: int
	offset: int
	model_config = ConfigDict(from_attributes=True)


class ProductSortEnum(str, Enum):
	price_asc = "price_asc"
	price_desc = "price_desc"
	popularity = "popularity"
	new = "new"
