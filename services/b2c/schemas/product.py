import uuid
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from database.models import ProductStatusEnum
from schemas.characteristic import Characteristic
from schemas.image import Image
from schemas.sku import Sku


class ProductShort(BaseModel):
	id: uuid.UUID
	title: str
	image: str = Field(format="uri")
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


SimilarProductsResponse = ProductShortListResponse
