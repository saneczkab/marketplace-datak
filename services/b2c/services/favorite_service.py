import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import crud.favorite as favorite_crud
from crud.review import ProductReviewStats
from database.models.catalog.base import Category, Product
from database.models.catalog.variants import Sku
from exceptions.product import ProductNotFoundError
from schemas.catalog import (
	CatalogProductCard,
	CatalogProductSeller,
	CategoryRef,
	ImageRef,
	PaginatedCatalogProducts,
)


def _build_category_ref(
	category_id: uuid.UUID, categories_map: dict[uuid.UUID, Category]
) -> CategoryRef:
	chain: list[Category] = []
	seen: set[uuid.UUID] = set()
	current_id: uuid.UUID | None = category_id

	while current_id is not None and current_id not in seen:
		seen.add(current_id)
		category = categories_map.get(current_id)
		if category is None:
			break
		chain.append(category)
		current_id = category.parent_id

	path_categories = list(reversed(chain))
	if not path_categories:
		return CategoryRef(
			id=category_id,
			name="",
			parent_id=None,
			level=0,
			path=[],
		)

	leaf = path_categories[-1]
	return CategoryRef(
		id=leaf.id,
		name=leaf.name,
		parent_id=leaf.parent_id,
		level=len(path_categories) - 1,
		path=[category.name for category in path_categories],
	)


def _product_images(product: Product) -> list[ImageRef]:
	images = sorted(product.images or [], key=lambda image: image.ordering)
	return [
		ImageRef(
			id=image.id,
			url=image.url,
			alt="",
			ordering=image.ordering,
			is_main=index == 0,
		)
		for index, image in enumerate(images)
	]


def _sku_stats(skus: list[Sku]) -> tuple[int, bool]:
	available_skus = [sku for sku in skus if sku.active_quantity > 0]
	if not available_skus:
		return 0, False
	return min(sku.price for sku in available_skus), True


def _build_catalog_product_card(
	product: Product,
	categories_map: dict[uuid.UUID, Category],
	review_stats: ProductReviewStats | None,
) -> CatalogProductCard:
	skus = list(product.skus or [])
	min_price, has_stock = _sku_stats(skus)

	return CatalogProductCard(
		id=product.id,
		name=product.title,
		slug=product.slug,
		category=_build_category_ref(product.category_id, categories_map),
		min_price=min_price,
		old_price=None,
		has_stock=has_stock,
		rating=review_stats.rating if review_stats else None,
		reviews_count=review_stats.reviews_count if review_stats else 0,
		images=_product_images(product),
		seller=CatalogProductSeller(
			id=product.seller_id,
			display_name=product.seller.company_name,
		),
	)


def _build_catalog_product_cards(
	products: list[Product],
	categories_map: dict[uuid.UUID, Category],
	review_stats_by_product: dict[uuid.UUID, ProductReviewStats],
) -> list[CatalogProductCard]:
	if not products:
		return []

	return [
		_build_catalog_product_card(
			product,
			categories_map,
			review_stats_by_product.get(product.id),
		)
		for product in products
	]


async def get_favorites_list(
	db: AsyncSession, user_id: uuid.UUID, limit: int, offset: int
) -> PaginatedCatalogProducts:
	data = await favorite_crud.get_available_favorites_data(db, user_id, limit, offset)
	items = _build_catalog_product_cards(
		data.products, data.categories_map, data.review_stats_by_product
	)
	return PaginatedCatalogProducts(
		items=items,
		total_count=data.total_count,
		limit=limit,
		offset=offset,
	)


async def add_to_favorites(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> None:
	if await favorite_crud.get_favorite(db, user_id, product_id):
		return

	if not await favorite_crud.check_product_exists_and_available(db, product_id):
		raise ProductNotFoundError("Товар не найден")

	await favorite_crud.add_favorite(db, user_id, product_id)


async def remove_from_favorites(
	db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> None:
	await favorite_crud.remove_favorite(db, user_id, product_id)
