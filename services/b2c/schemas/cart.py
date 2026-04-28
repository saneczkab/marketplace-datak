import uuid
from typing import Optional
from pydantic import BaseModel, Field


class CartItem(BaseModel):
	"""Single cart item with enriched product data"""

	item_id: uuid.UUID = Field(description="ID позиции в корзине")
	sku_id: uuid.UUID = Field(description="ID варианта товара (SKU)")
	product_id: uuid.UUID = Field(description="ID товара")
	product_title: str = Field(description="Название товара")
	sku_name: str = Field(description="Название варианта")
	image_url: Optional[str] = Field(None, description="URL изображения SKU")
	unit_price: int = Field(description="Актуальная цена за единицу в копейках")
	quantity: int = Field(ge=1, description="Количество в корзине")
	available_stock: int = Field(ge=0, description="Текущий остаток на складе")
	line_total: int = Field(description="Сумма по позиции = unit_price × quantity")
	available: bool = Field(description="Доступен ли товар для покупки")
	unavailable_reason: Optional[str] = Field(
		None,
		description="Причина недоступности: OUT_OF_STOCK, PRODUCT_BLOCKED, PRODUCT_DELISTED",
	)


class CartSummary(BaseModel):
	"""Cart summary information"""

	total_amount: int = Field(description="Сумма по доступным товарам в копейках")
	total_items: int = Field(description="Количество уникальных позиций в корзине")
	total_quantity: int = Field(description="Суммарное количество единиц товара")
	available_items: int = Field(description="Количество доступных позиций")
	has_unavailable_items: bool = Field(description="Есть ли недоступные позиции")
	checkout_ready: bool = Field(description="Можно ли переходить к оформлению")
	currency: str = Field(default="RUB", description="Валюта корзины")


class CheckoutItem(BaseModel):
	"""Item for checkout payload"""

	product_id: uuid.UUID
	sku_id: uuid.UUID
	quantity: int
	unit_price: int
	line_total: int


class CheckoutPayload(BaseModel):
	"""Data for checkout process"""

	items: list[CheckoutItem]
	total_amount: int
	currency: str = "RUB"


class CartResponse(BaseModel):
	"""Complete cart response"""

	items: list[CartItem]
	summary: CartSummary
	checkout_payload: CheckoutPayload
