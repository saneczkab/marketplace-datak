import uuid


async def notification_product_blocked(
	user_id: uuid.UUID, sku_id: uuid.UUID, hard_blocked: bool
) -> None:
	"""Notofication placeholder. Will place notification into db"""
	pass


async def notification_sku_out_of_stock(sku_id: uuid.UUID, user_id: uuid.UUID) -> None:
	pass


async def notification_sku_back_in_stock(sku_id: uuid.UUID) -> None:
	pass


async def notification_sku_price_change(
	sku_id: uuid.UUID, old_price: int, new_price: int
) -> None:
	"""
	Also needs to trigger price-drop notifications or something
	"""
	pass


async def notification_product_deleted() -> None:
	pass
