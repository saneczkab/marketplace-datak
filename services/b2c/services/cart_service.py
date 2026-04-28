import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

import crud.cart as cart_crud
from database.models.catalog.base import ProductStatusEnum
from schemas.cart import (
	CartItem,
	CartResponse,
	CartSummary,
	CheckoutItem,
	CheckoutPayload,
)


async def get_cart(
	db: AsyncSession, user_id: Optional[uuid.UUID], session_id: Optional[str]
) -> CartResponse:
	"""
	Get cart with enriched product data.
	Returns cart items, summary, and checkout payload.
	"""
	enriched_items = await cart_crud.get_cart_items_with_details(
		db, user_id, session_id
	)

	if not enriched_items:
		# Empty cart
		return CartResponse(
			items=[],
			summary=CartSummary(
				total_amount=0,
				total_items=0,
				total_quantity=0,
				available_items=0,
				has_unavailable_items=False,
				checkout_ready=False,
				currency="RUB",
			),
			checkout_payload=CheckoutPayload(items=[], total_amount=0, currency="RUB"),
		)

	cart_items = []
	checkout_items = []
	total_amount = 0
	total_quantity = 0
	available_items_count = 0
	has_unavailable = False

	for cart_item, sku, product, image_url in enriched_items:
		# Determine availability
		available = True
		unavailable_reason = None

		if product.status == ProductStatusEnum.BLOCKED:
			available = False
			unavailable_reason = "PRODUCT_BLOCKED"
		elif sku.active_quantity == 0:
			available = False
			unavailable_reason = "OUT_OF_STOCK"

		# Calculate line total
		line_total = sku.price * cart_item.quantity if available else 0

		# Build cart item
		item = CartItem(
			item_id=cart_item.id,
			sku_id=sku.id,
			product_id=product.id,
			product_title=product.title,
			sku_name=sku.name,
			image_url=image_url,
			unit_price=sku.price,
			quantity=cart_item.quantity,
			available_stock=sku.active_quantity,
			line_total=line_total,
			available=available,
			unavailable_reason=unavailable_reason,
		)
		cart_items.append(item)

		# Update counters
		total_quantity += cart_item.quantity
		if available:
			total_amount += line_total
			available_items_count += 1
			checkout_items.append(
				CheckoutItem(
					product_id=product.id,
					sku_id=sku.id,
					quantity=cart_item.quantity,
					unit_price=sku.price,
					line_total=line_total,
				)
			)
		else:
			has_unavailable = True

	summary = CartSummary(
		total_amount=total_amount,
		total_items=len(cart_items),
		total_quantity=total_quantity,
		available_items=available_items_count,
		has_unavailable_items=has_unavailable,
		checkout_ready=not has_unavailable and len(cart_items) > 0,
		currency="RUB",
	)

	checkout_payload = CheckoutPayload(
		items=checkout_items, total_amount=total_amount, currency="RUB"
	)

	return CartResponse(
		items=cart_items, summary=summary, checkout_payload=checkout_payload
	)
