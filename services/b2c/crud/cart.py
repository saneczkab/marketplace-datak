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
