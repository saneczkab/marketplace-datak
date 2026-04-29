import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

import crud.cart as cart_crud
from database.models.cart.item import CartItem as CartItemDB
from database.models.catalog.base import Product, ProductStatusEnum
from database.models.catalog.variants import Sku
from exceptions.cart import CartItemNotFoundError
from exceptions.sku import SkuNotFoundError
from schemas.cart import (
	CartItem,
	CartMutationResponse,
	CartResponse,
	CartSummary,
	CartValidationIssue,
	CartValidationResponse,
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


async def _build_cart_item_with_details(
	cart_item_db: CartItemDB,
	sku: Sku,
	product: Product,
	image_url: Optional[str],
) -> CartItem:
	"""Helper to build enriched CartItem from DB models"""
	available = True
	unavailable_reason = None

	if product.status == ProductStatusEnum.BLOCKED:
		available = False
		unavailable_reason = "PRODUCT_BLOCKED"
	elif sku.active_quantity == 0:
		available = False
		unavailable_reason = "OUT_OF_STOCK"

	line_total = sku.price * cart_item_db.quantity if available else 0

	return CartItem(
		item_id=cart_item_db.id,
		sku_id=sku.id,
		product_id=product.id,
		product_title=product.title,
		sku_name=sku.name,
		image_url=image_url,
		unit_price=sku.price,
		quantity=cart_item_db.quantity,
		available_stock=sku.active_quantity,
		line_total=line_total,
		available=available,
		unavailable_reason=unavailable_reason,
	)


async def _calculate_cart_summary(
	db: AsyncSession, user_id: Optional[uuid.UUID], session_id: Optional[str]
) -> CartSummary:
	"""Calculate cart summary for user/session"""
	enriched_items = await cart_crud.get_cart_items_with_details(
		db, user_id, session_id
	)

	if not enriched_items:
		return CartSummary(
			total_amount=0,
			total_items=0,
			total_quantity=0,
			available_items=0,
			has_unavailable_items=False,
			checkout_ready=False,
			currency="RUB",
		)

	total_amount = 0
	total_quantity = 0
	available_items_count = 0
	has_unavailable = False

	for cart_item, sku, product, _ in enriched_items:
		available = True
		if product.status == ProductStatusEnum.BLOCKED or sku.active_quantity == 0:
			available = False
			has_unavailable = True

		total_quantity += cart_item.quantity
		if available:
			total_amount += sku.price * cart_item.quantity
			available_items_count += 1

	return CartSummary(
		total_amount=total_amount,
		total_items=len(enriched_items),
		total_quantity=total_quantity,
		available_items=available_items_count,
		has_unavailable_items=has_unavailable,
		checkout_ready=not has_unavailable and len(enriched_items) > 0,
		currency="RUB",
	)


async def add_cart_item(
	db: AsyncSession,
	user_id: Optional[uuid.UUID],
	session_id: Optional[str],
	sku_id: uuid.UUID,
	quantity: int,
) -> CartMutationResponse:
	"""Add item to cart or update quantity if exists"""
	# Check if SKU exists
	sku = await cart_crud.get_sku_by_id(db, sku_id)
	if not sku:
		raise SkuNotFoundError(f"SKU with id {sku_id} not found")

	# Check product status
	if sku.product.status == ProductStatusEnum.BLOCKED:
		raise ValueError("SKU_NOT_AVAILABLE: Товар недоступен для покупки")

	# Check stock availability
	existing_item = await cart_crud.get_cart_item_by_sku(
		db, user_id, session_id, sku_id
	)
	new_quantity = quantity if not existing_item else existing_item.quantity + quantity

	if new_quantity > sku.active_quantity:
		raise ValueError(
			f"INSUFFICIENT_STOCK: Нельзя добавить {quantity}, доступно только {sku.active_quantity}"
		)

	# Create or update cart item
	if existing_item:
		cart_item_db = await cart_crud.update_cart_item_quantity(
			db, existing_item, new_quantity
		)
		message = "SKU уже был в корзине, количество увеличено"
	else:
		cart_item_db = await cart_crud.create_cart_item(
			db, user_id, session_id, sku_id, quantity
		)
		message = "Товар добавлен как новая позиция"

	# Get enriched item details
	enriched_items = await cart_crud.get_cart_items_with_details(
		db, user_id, session_id
	)
	cart_item_enriched = None
	for ci, s, p, img in enriched_items:
		if ci.id == cart_item_db.id:
			cart_item_enriched = await _build_cart_item_with_details(db, ci, s, p, img)
			break

	# Calculate summary
	summary = await _calculate_cart_summary(db, user_id, session_id)

	return CartMutationResponse(
		message=message, item=cart_item_enriched, summary=summary
	)


async def get_cart_item(
	db: AsyncSession,
	user_id: Optional[uuid.UUID],
	session_id: Optional[str],
	item_id: uuid.UUID,
) -> CartItem:
	"""Get single cart item with enriched data"""
	cart_item_db = await cart_crud.get_cart_item_by_id(db, item_id)
	if not cart_item_db:
		raise CartItemNotFoundError(f"Cart item with id {item_id} not found")

	# Check ownership
	if user_id and cart_item_db.user_id != user_id:
		raise CartItemNotFoundError(f"Cart item with id {item_id} not found")
	if session_id and cart_item_db.session_id != session_id:
		raise CartItemNotFoundError(f"Cart item with id {item_id} not found")

	# Get enriched details
	enriched_items = await cart_crud.get_cart_items_with_details(
		db, user_id, session_id
	)
	for ci, sku, product, img in enriched_items:
		if ci.id == item_id:
			return await _build_cart_item_with_details(db, ci, sku, product, img)

	raise CartItemNotFoundError(f"Cart item with id {item_id} not found")


async def update_cart_item(
	db: AsyncSession,
	user_id: Optional[uuid.UUID],
	session_id: Optional[str],
	item_id: uuid.UUID,
	quantity: int,
) -> CartMutationResponse:
	"""Update cart item quantity"""
	cart_item_db = await cart_crud.get_cart_item_by_id(db, item_id)
	if not cart_item_db:
		raise CartItemNotFoundError(f"Cart item with id {item_id} not found")

	# Check ownership (403 if not owner)
	if user_id and cart_item_db.user_id != user_id:
		raise PermissionError("ACCESS_DENIED: Нет доступа к этой позиции корзины")
	if session_id and cart_item_db.session_id != session_id:
		raise PermissionError("ACCESS_DENIED: Нет доступа к этой позиции корзины")

	# Check SKU availability
	sku = await cart_crud.get_sku_by_id(db, cart_item_db.sku_id)
	if not sku:
		raise SkuNotFoundError(f"SKU with id {cart_item_db.sku_id} not found")

	if sku.product.status == ProductStatusEnum.BLOCKED:
		raise ValueError(
			"PRODUCT_NOT_AVAILABLE: Товар недоступен и не может быть обновлён"
		)

	if quantity > sku.active_quantity:
		raise ValueError(
			f"INSUFFICIENT_STOCK: Нельзя установить {quantity}, доступно только {sku.active_quantity}"
		)

	# Update quantity
	cart_item_db = await cart_crud.update_cart_item_quantity(db, cart_item_db, quantity)

	# Get enriched details
	enriched_items = await cart_crud.get_cart_items_with_details(
		db, user_id, session_id
	)
	cart_item_enriched = None
	for ci, s, p, img in enriched_items:
		if ci.id == item_id:
			cart_item_enriched = await _build_cart_item_with_details(db, ci, s, p, img)
			break

	# Calculate summary
	summary = await _calculate_cart_summary(db, user_id, session_id)

	return CartMutationResponse(
		message="Количество обновлено", item=cart_item_enriched, summary=summary
	)


async def delete_cart_item(
	db: AsyncSession,
	user_id: Optional[uuid.UUID],
	session_id: Optional[str],
	item_id: uuid.UUID,
) -> None:
	"""Delete cart item"""
	cart_item_db = await cart_crud.get_cart_item_by_id(db, item_id)
	if not cart_item_db:
		raise CartItemNotFoundError(f"Cart item with id {item_id} not found")

	# Check ownership
	if user_id and cart_item_db.user_id != user_id:
		raise CartItemNotFoundError(f"Cart item with id {item_id} not found")
	if session_id and cart_item_db.session_id != session_id:
		raise CartItemNotFoundError(f"Cart item with id {item_id} not found")

	await cart_crud.delete_cart_item(db, cart_item_db)


async def validate_cart(
	db: AsyncSession, user_id: Optional[uuid.UUID], cart_item_ids: Optional[list[str]]
) -> CartValidationResponse:
	"""Validate cart items availability"""
	enriched_items = await cart_crud.get_cart_items_with_details(db, user_id, None)

	if cart_item_ids:
		# Filter by specific item IDs
		item_ids_set = set(cart_item_ids)
		enriched_items = [
			item for item in enriched_items if str(item[0].id) in item_ids_set
		]

	if not enriched_items:
		return CartValidationResponse(
			is_valid=True,
			can_checkout=False,
			total_items=0,
			validation_timestamp=datetime.now(timezone.utc).isoformat(),
			issues=[],
		)

	issues = []
	has_critical = False

	for cart_item, sku, product, _ in enriched_items:
		issue = None

		if product.status == ProductStatusEnum.BLOCKED:
			issue = CartValidationIssue(
				cart_item_id=str(cart_item.id),
				sku_id=sku.id,
				issue_type="BLOCKED",
				severity="critical",
				message="Товар заблокирован модератором и недоступен для покупки",
				details={
					"product_id": str(product.id),
					"product_title": product.title,
					"sku_name": sku.name,
					"current_status": product.status.value,
				},
			)
			has_critical = True
		elif sku.active_quantity == 0:
			issue = CartValidationIssue(
				cart_item_id=str(cart_item.id),
				sku_id=sku.id,
				issue_type="OUT_OF_STOCK",
				severity="critical",
				message="Товар отсутствует в наличии",
				details={
					"product_id": str(product.id),
					"product_title": product.title,
					"sku_name": sku.name,
					"requested_quantity": cart_item.quantity,
					"available_quantity": 0,
				},
			)
			has_critical = True
		elif cart_item.quantity > sku.active_quantity:
			issue = CartValidationIssue(
				cart_item_id=str(cart_item.id),
				sku_id=sku.id,
				issue_type="INSUFFICIENT_STOCK",
				severity="warning",
				message="Доступно меньше товара, чем в корзине",
				details={
					"product_id": str(product.id),
					"product_title": product.title,
					"sku_name": sku.name,
					"requested_quantity": cart_item.quantity,
					"available_quantity": sku.active_quantity,
				},
			)

		if issue:
			issues.append(issue)

	return CartValidationResponse(
		is_valid=len(issues) == 0,
		can_checkout=not has_critical and len(enriched_items) > 0,
		total_items=len(enriched_items),
		validation_timestamp=datetime.now(timezone.utc).isoformat(),
		issues=issues,
	)
