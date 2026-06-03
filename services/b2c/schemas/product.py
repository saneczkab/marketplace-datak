import uuid
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from database.models import ProductStatusEnum
from schemas.category import CategoryInFavorite
from schemas.characteristic import Characteristic, CharacteristicInFavorite
from schemas.image import Image, ImageInFavorite
from schemas.sku import Sku, SkuInFavorite


class ProductCardCharacteristic(BaseModel):
	model_config = ConfigDict(from_attributes=True)
	name: str
	value: str


class ProductCardImage(BaseModel):
	model_config = ConfigDict(from_attributes=True)
	url: str
	ordering: int = 0


class ProductCardSku(BaseModel):
	id: uuid.UUID
	name: str
	price: int
	discount: int = 0
	active_quantity: int
	in_stock: bool
	image: str | None = None
	characteristics: list[ProductCardCharacteristic] = []


class ProductCard(BaseModel):
	id: uuid.UUID
	slug: str
	title: str
	description: str | None
	images: list[ProductCardImage]
	status: ProductStatusEnum
	characteristics: list[ProductCardCharacteristic]
	skus: list[ProductCardSku]


class ProductShort(BaseModel):
	id: uuid.UUID
	title: str
	image: str = Field(json_schema_extra={"format": "uri"})
	price: float
	in_stock: bool
	is_in_cart: bool
	model_config = ConfigDict(from_attributes=True)


class Product(BaseModel):
	id: uuid.UUID
	slug: str
	title: str
	description: str
	images: List[Image]
	status: ProductStatusEnum
	characteristics: List[Characteristic]
	skus: List[Sku]
	model_config = ConfigDict(from_attributes=True)


class ProductShortListResponse(BaseModel):
	total_count: int
	limit: int
	offset: int
	items: List[ProductShort]
	model_config = ConfigDict(from_attributes=True)


class ProductInFavorite(BaseModel):
	id: uuid.UUID
	title: str
	description: str | None
	status: str
	category: CategoryInFavorite
	images: List[ImageInFavorite]
	characteristics: List[CharacteristicInFavorite]
	skus: List[SkuInFavorite]
	model_config = ConfigDict(from_attributes=True)
