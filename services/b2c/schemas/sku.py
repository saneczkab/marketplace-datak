import uuid

from pydantic import BaseModel

from schemas.characteristic import Characteristic
from schemas.image import Image


class Sku(BaseModel):
	id: uuid.UUID
	name: str
	price: float
	quantity: int
	characteristics: list[Characteristic]
	images: list[Image]


class SkuShort(BaseModel):
	name: str
	price: float
	image: Image
