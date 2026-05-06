import uuid
from collections import deque
from typing import List, Tuple, Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Sku
from database.models.catalog.base import Category, Product
from schemas.sku import Sku as SkuSchema
from exceptions.product import ProductNotFoundError


async def get_category_descendants(
	db: AsyncSession, category_id: uuid.UUID
) -> list[uuid.UUID]:
	res = await db.execute(select(Category.id, Category.parent_id))
	cats = res.all()

	children_by_parent: dict[uuid.UUID | None, list[uuid.UUID]] = {}
	for child_id, parent_id in cats:
		children_by_parent.setdefault(parent_id, []).append(child_id)

	collected: list[uuid.UUID] = []
	seen: set[uuid.UUID] = set()
	queue = deque([category_id])

	while queue:
		current_id = queue.popleft()
		if current_id in seen:
			continue
		seen.add(current_id)
		collected.append(current_id)
		queue.extend(children_by_parent.get(current_id, []))

	return collected


async def count_products_in_category(db: AsyncSession, category_id: uuid.UUID) -> int:
	category_ids = await get_category_descendants(db, category_id)
	result = await db.execute(
		select(func.count(Product.id)).where(Product.category_id.in_(category_ids))
	)
	return result.scalar() or 0


async def get_product_skus(
	db: AsyncSession, product_id: uuid.UUID
) -> List[SkuSchema] | None:
	"""
	Returns a list of skus for a given product ID.
	:param db: database session
	:param product_id: product ID
	:return: list of skus or None if not found
	"""
	result = await db.execute(
		select(Sku)
		.where(Sku.product_id == product_id)
		.options(selectinload(Sku.images))
	)
	return list(result.scalars().all())


async def get_products_list(
	db: AsyncSession,
	limit: int,
	offset: int,
	category_id: Optional[uuid.UUID],
	filters: Optional[dict],
	sort: str,
	search: Optional[str],
) -> Tuple[List[Product], int]:
	from database.models.catalog.base import ProductStatusEnum

	query = select(Product).options(selectinload(Product.images))
	count_query = select(func.count(func.distinct(Product.id)))

	# Условие видимости: status = MODERATED AND active_quantity > 0
	# Используем exists() чтобы избежать дубликатов продуктов
	query = query.where(
		Product.status == ProductStatusEnum.MODERATED,
		Product.id.in_(select(Sku.product_id).where(Sku.active_quantity > 0)),
	)

	count_query = count_query.where(
		Product.status == ProductStatusEnum.MODERATED,
		Product.id.in_(select(Sku.product_id).where(Sku.active_quantity > 0)),
	)

	if category_id:
		category_ids = await get_category_descendants(db, category_id)
		query = query.where(Product.category_id.in_(category_ids))
		count_query = count_query.where(Product.category_id.in_(category_ids))

	if filters:
		for key, value in filters.items():
			column = getattr(Product, key, None)
			if column is not None:
				query = query.where(column == value)
				count_query = count_query.where(column == value)

	if search and len(search.strip()) >= 3:
		term = f"%{search.strip()}%"
		query = query.where(
			or_(Product.title.ilike(term), Product.description.ilike(term))
		)
		count_query = count_query.where(
			or_(Product.title.ilike(term), Product.description.ilike(term))
		)

	sort_map = {
		"rating": Product.created_at.desc(),  # TODO: добавить поле rating когда будет # noqa
		"popularity": Product.created_at.desc(),  # TODO: добавить поле popularity когда будет # noqa
		"price_asc": Product.created_at.desc(),  # TODO: сортировка по цене SKU # noqa
		"price_desc": Product.created_at.desc(),  # TODO: сортировка по цене SKU # noqa
		"date_desc": Product.created_at.desc(),
		"discount_desc": Product.created_at.desc(),  # TODO: добавить поле discount когда будет # noqa
	}
	query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

	query = query.offset(offset).limit(limit)

	products = list((await db.execute(query)).scalars().all())
	total = (await db.execute(count_query)).scalar() or 0

	return products, total


async def get_product_full(db: AsyncSession, id: uuid.UUID) -> Optional[Product]:
	stmt = (
		select(Product)
		.where(Product.id == id)
		.options(
			selectinload(Product.images),
			selectinload(Product.characteristics),
			selectinload(Product.skus).selectinload(Sku.images),
			selectinload(Product.skus).selectinload(Sku.characteristics),
		)
	)
	return (await db.execute(stmt)).scalar_one_or_none()


async def get_similar_products(
	db: AsyncSession,
	category_id: uuid.UUID,
	exclude_id: uuid.UUID,
	limit: int,
	offset: int,
) -> Tuple[List[Product], int]:
	category_ids = await get_category_descendants(db, category_id)
	query = (
		select(Product)
		.options(selectinload(Product.images))
		.where(and_(Product.category_id.in_(category_ids), Product.id != exclude_id))
	)
	count_query = select(func.count(Product.id)).where(
		and_(Product.category_id.in_(category_ids), Product.id != exclude_id)
	)

	query = query.order_by(Product.created_at.desc()).offset(offset).limit(limit)

	products = list((await db.execute(query)).scalars().all())
	total = (await db.execute(count_query)).scalar() or 0

	return products, total


async def get_product_category_id(db: AsyncSession, product_id: uuid.UUID) -> uuid.UUID:
	result = await db.execute(
		select(Product.category_id).where(Product.id == product_id)
	)
	category_id = result.scalar()
	if not category_id:
		raise ProductNotFoundError(f"Product with id {product_id} not found")
	return category_id


async def count_products_by_filter(
	db: AsyncSession, category_id: uuid.UUID, filter_id: uuid.UUID, filter_value: str
) -> int:
	"""
	Подсчитывает количество видимых товаров в категории с определенным значением фильтра.
	"""

	category_ids = await get_category_descendants(db, category_id)

	# TODO: Реализовать подсчет по фильтрам когда будет связь Product <-> FilterValues
	# Пока возвращаем 0, так как связи между товарами и значениями фильтров нет в текущей схеме
	return 0
