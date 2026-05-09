import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict
from schemas.product import ProductInFavorite


class FavoriteItem(BaseModel):
	product: ProductInFavorite
	added_at: datetime
	model_config = ConfigDict(from_attributes=True)


class FavoritesResponse(BaseModel):
	items: List[FavoriteItem]
	total: int
	model_config = ConfigDict(from_attributes=True)


class FavoriteMutationResponse(BaseModel):
	product_id: uuid.UUID
	user_id: uuid.UUID
	added_at: datetime
	message: str
	model_config = ConfigDict(from_attributes=True)
