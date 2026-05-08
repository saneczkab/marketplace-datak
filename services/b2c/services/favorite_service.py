import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import crud.favorite as favorite_crud
from exceptions.product import ProductNotFoundError
from schemas.favorite import FavoritesResponse, FavoriteItem
from schemas.product import ProductInFavorite


async def get_favorites_list(
	db: AsyncSession, user_id: uuid.UUID, limit: int, offset: int
) -> FavoritesResponse:
	favorites, total_count = await favorite_crud.get_available_favorites(
		db, user_id, limit, offset
	)

	items = [
		FavoriteItem(
			product=ProductInFavorite.model_validate(favorite.product),
			added_at=favorite.added_at,
		)
		for favorite in favorites
	]
	return FavoritesResponse(items=items, total=total_count)


async def add_to_favorites(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> dict:
	product_exists = await favorite_crud.check_product_exists_and_available(
		db, product_id
	)
	if not product_exists:
		raise ProductNotFoundError("Товар не найден")

	existing = await favorite_crud.get_favorite(db, user_id, product_id)
	if existing:
		return {"is_new": False, "favorite": existing}

	favorite = await favorite_crud.add_favorite(db, user_id, product_id)
	await db.commit()
	return {"is_new": True, "favorite": favorite}


async def remove_from_favorites(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> None:
	product_exists = await favorite_crud.check_product_exists_and_available(
		db, product_id
	)
	if not product_exists:
		raise ProductNotFoundError("Товар не найден")

	await favorite_crud.remove_favorite(db, user_id, product_id)
	await db.commit()
