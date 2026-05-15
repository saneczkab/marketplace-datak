import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class Category(BaseModel):
	id: uuid.UUID
	name: str


class Image(BaseModel):
	url: str
	ordering: int


class Characteristic(BaseModel):
	name: str
	value: str


class SKU(BaseModel):
	id: uuid.UUID
	name: str
	price: int
	active_quantity: int
	characteristics: list[Characteristic] = []


class ProductSchema(BaseModel):
	id: uuid.UUID
	title: str
	description: str
	status: str
	category: Category
	images: list[Image] = []
	characteristics: list[Characteristic] = []
	skus: list[SKU] = []


class CollectionBase(BaseModel):
	id: uuid.UUID
	title: str
	description: Optional[str] = None
	cover_image_url: Optional[str] = None
	target_url: Optional[str] = None
	priority: int
	start_date: Optional[date] = None


class CollectionMetadata(BaseModel):
	total_count: int
	limit: int
	offset: int


class CollectionsResponse(BaseModel):
	metadata: CollectionMetadata
	collections: list[CollectionBase]


class CollectionProductsResponse(BaseModel):
	collection_title: str
	total_products: int
	items: list[ProductSchema]
	unavailable_ids: list[uuid.UUID] = Field(
		default_factory=list,
		description="ID товаров, которые есть в подборке, но удалены/недоступны в каталоге",
	)
