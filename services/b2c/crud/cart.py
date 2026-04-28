import uuid
from typing import Optional, Tuple

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.cart.item import CartItem
from database.models.catalog.base import Product
from database.models.catalog.variants import Image, Sku


async def get_cart_items_with_details(
	db: AsyncSession, user_id: Optional[uuid.UUID], session_id: Optional[str]
) -> list[tuple[CartItem, Sku, Product, Optional[str]]]:
	"""
	Get cart items with enriched product/sku data.
	Returns list of tuples: (CartItem, Sku, Product, image_url)
	"""
	query = (
		select(CartItem, Sku, Product)
		.join(Sku, CartItem.sku_id == Sku.id)
		.join(Product, Sku.product_id == Product.id)
		.options(
			selectinload(Product.images),
			selectinload(Product.characteristics),
		)
	)

	if user_id:
		query = query.where(CartItem.user_id == user_id)
	elif session_id:
		query = query.where(CartItem.session_id == session_id)

	result: Result[Tuple[CartItem, Sku, Product]] = await db.execute(query)
	rows = result.all()

	# Enrich with image URLs
	enriched_items = []
	for cart_item, sku, product in rows:
		# Try to find SKU-specific image first
		image_url = None
		sku_image_result: Result[Tuple[str]] = await db.execute(
			select(Image.url)
			.where(Image.sku_id == sku.id)
			.order_by(Image.ordering)
			.limit(1)
		)
		sku_image = sku_image_result.scalar()

		if sku_image:
			image_url = sku_image
		elif product.images:
			# Fallback to first product image
			sorted_images = sorted(product.images, key=lambda img: img.ordering)
			if sorted_images:
				image_url = sorted_images[0].url

		enriched_items.append((cart_item, sku, product, image_url))

	return enriched_items


async def clear_cart(
	db: AsyncSession, user_id: Optional[uuid.UUID], session_id: Optional[str]
) -> None:
	"""Delete all cart items for user or session"""
	from sqlalchemy import delete

	query = delete(CartItem)

	if user_id:
		query = query.where(CartItem.user_id == user_id)
	elif session_id:
		query = query.where(CartItem.session_id == session_id)

	await db.execute(query)
	await db.commit()


async def get_cart_item_by_id(
	db: AsyncSession, item_id: uuid.UUID
) -> Optional[CartItem]:
	"""Get cart item by ID"""
	result: Result[Tuple[CartItem]] = await db.execute(
		select(CartItem).where(CartItem.id == item_id)
	)
	return result.scalar_one_or_none()


async def get_sku_by_id(db: AsyncSession, sku_id: uuid.UUID) -> Optional[Sku]:
	"""Get SKU by ID with product relationship"""
	result: Result[Tuple[Sku]] = await db.execute(
		select(Sku).where(Sku.id == sku_id).options(selectinload(Sku.product))
	)
	return result.scalar_one_or_none()


async def get_cart_item_by_sku(
	db: AsyncSession,
	user_id: Optional[uuid.UUID],
	session_id: Optional[str],
	sku_id: uuid.UUID,
) -> Optional[CartItem]:
	"""Find existing cart item for user/session and SKU"""
	query = select(CartItem).where(CartItem.sku_id == sku_id)

	if user_id:
		query = query.where(CartItem.user_id == user_id)
	elif session_id:
		query = query.where(CartItem.session_id == session_id)

	result: Result[Tuple[CartItem]] = await db.execute(query)
	return result.scalar_one_or_none()


async def create_cart_item(
	db: AsyncSession,
	user_id: Optional[uuid.UUID],
	session_id: Optional[str],
	sku_id: uuid.UUID,
	quantity: int,
) -> CartItem:
	"""Create new cart item"""
	cart_item = CartItem(
		user_id=user_id, session_id=session_id, sku_id=sku_id, quantity=quantity
	)
	db.add(cart_item)
	await db.commit()
	await db.refresh(cart_item)
	return cart_item


async def update_cart_item_quantity(
	db: AsyncSession, cart_item: CartItem, quantity: int
) -> CartItem:
	"""Update cart item quantity"""
	cart_item.quantity = quantity
	await db.commit()
	await db.refresh(cart_item)
	return cart_item


async def delete_cart_item(db: AsyncSession, cart_item: CartItem) -> None:
	"""Delete cart item"""
	await db.delete(cart_item)
	await db.commit()
