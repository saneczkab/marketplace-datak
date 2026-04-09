import uuid

from pydantic import BaseModel, ConfigDict

from schemas.characteristic import Characteristic
from schemas.image import Image


class Sku(BaseModel):
	model_config = ConfigDict(from_attributes=True)

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
