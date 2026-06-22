import uuid
from dataclasses import dataclass

from fastapi import FastAPI

from clients.b2b_client import get_b2b_client
from exceptions.order import B2BUnavailableError, ReserveFailedError
from database.models.orders.order import Order, OrderStatusEnum
from database.models.orders.order_item import OrderItem
from database.models.personal.address import Address
from database.models.personal.payment_method import PaymentMethod
from database.models.cart.item import CartItem
from database.models.identity.user import User
from database.models.catalog.base import Category, Product, ProductStatusEnum
from database.models.catalog.variants import Sku
from tests.factories.order import (
	OrderFactory,
	OrderItemFactory,
	AddressFactory,
	OrderStatusHistoryFactory,
	PaymentMethodFactory,
)
from tests.factories.catalog import (
	CartItemFactory,
	CategoryFactory,
	ProductFactory,
	SkuFactory,
)
from tests.factories.user import UserFactory
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class FakeB2BClient:
	def __init__(
		self,
		behavior: str = "ok",
		unreserve_behavior: str | None = None,
		failed_items: list[dict] | None = None,
	) -> None:
		self.behavior = behavior
		self.unreserve_behavior = (
			unreserve_behavior if unreserve_behavior is not None else behavior
		)
		self.failed_items = failed_items if failed_items is not None else []
		self.calls: list[dict] = []
		self.unreserve_calls: list[dict] = []

	async def reserve(
		self,
		idempotency_key: uuid.UUID,
		order_id: uuid.UUID,
		items: list[dict],
	) -> None:
		self.calls.append(
			{
				"idempotency_key": idempotency_key,
				"order_id": order_id,
				"items": items,
			}
		)
		if self.behavior == "conflict":
			raise ReserveFailedError(self.failed_items)
		if self.behavior == "unavailable":
			raise B2BUnavailableError()

	async def unreserve(
		self,
		order_id: uuid.UUID,
		items: list[dict],
	) -> None:
		self.unreserve_calls.append({"order_id": order_id, "items": items})
		if self.unreserve_behavior == "unavailable":
			raise B2BUnavailableError()


def override_b2b_client(app: FastAPI, b2b_client: FakeB2BClient) -> FakeB2BClient:
	app.dependency_overrides[get_b2b_client] = lambda: b2b_client
	return b2b_client


@pytest.fixture(autouse=True)
def default_b2b_client(app: FastAPI) -> FakeB2BClient:
	client = FakeB2BClient("ok")
	app.dependency_overrides[get_b2b_client] = lambda: client
	yield client
	app.dependency_overrides.pop(get_b2b_client, None)


@dataclass(frozen=True, slots=True)
class OrderData:
	order: Order
	order_items: list[OrderItem]
	address: Address
	payment_method: PaymentMethod
	cart_items: list[CartItem]
	skus: list[Sku]
	product: Product


@dataclass(frozen=True, slots=True)
class CartData:
	user: User
	address: Address
	payment_method: PaymentMethod
	items: list[CartItem]
	category: Category
	product: Product
	sku: Sku


@pytest.fixture()
async def order_data(db_session: AsyncSession) -> OrderData:
	user = UserFactory.build()
	address = AddressFactory.build(user_id=user.id)
	payment_method = PaymentMethodFactory.build(user_id=user.id)
	category = CategoryFactory.build()
	product = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.MODERATED,
	)
	skus = [SkuFactory.build(product_id=product.id) for _ in range(3)]
	cart_items = [
		CartItemFactory.build(
			user_id=user.id,
			sku_id=sku.id,
			quantity=2,
			unit_price_at_add=sku.price,
		)
		for sku in skus
	]
	order = OrderFactory.build(
		buyer_id=user.id,
		address_id=address.id,
		payment_method_id=payment_method.id,
	)
	order_items = [
		OrderItemFactory.build(order_id=order.id, sku_id=sku.id, unit_price=sku.price)
		for sku in skus
	]
	order_status_history = OrderStatusHistoryFactory.build(
		order_id=order.id, status=OrderStatusEnum.PAID
	)

	db_session.add_all(
		[
			user,
			address,
			payment_method,
			category,
			product,
			*skus,
			*cart_items,
			order,
			*order_items,
			order_status_history,
		]
	)
	await db_session.commit()

	order_data_result = OrderData(
		order=order,
		order_items=order_items,
		address=address,
		payment_method=payment_method,
		cart_items=cart_items,
		skus=skus,
		product=product,
	)
	return order_data_result


@pytest.fixture()
async def partial_reserve_failure_data(db_session: AsyncSession) -> OrderData:
	user = UserFactory.build()
	address = AddressFactory.build(user_id=user.id)
	payment_method = PaymentMethodFactory.build(user_id=user.id)
	category = CategoryFactory.build()
	blocked_product = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.CREATED,
	)
	product = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.MODERATED,
	)
	skus = [
		SkuFactory.build(product_id=blocked_product.id),
		SkuFactory.build(product_id=product.id),
		SkuFactory.build(product_id=product.id),
	]
	cart_items = [
		CartItemFactory.build(
			user_id=user.id, sku_id=sku.id, quantity=2, unit_price_at_add=sku.price
		)
		for sku in skus
	]
	order = OrderFactory.build(
		buyer_id=user.id,
		address_id=address.id,
		payment_method_id=payment_method.id,
	)
	order_items = [OrderItemFactory.build(order_id=order.id) for _ in range(3)]
	db_session.add_all(
		[
			user,
			address,
			payment_method,
			category,
			blocked_product,
			product,
			*skus,
			*cart_items,
			order,
			*order_items,
		]
	)
	await db_session.commit()
	return OrderData(
		order=order,
		order_items=order_items,
		address=address,
		payment_method=payment_method,
		cart_items=cart_items,
		skus=skus,
		product=product,
	)


@pytest.fixture()
async def cart_validation_error_data(db_session: AsyncSession) -> OrderData:
	user = UserFactory.build()
	address = AddressFactory.build(user_id=user.id)
	payment_method = PaymentMethodFactory.build(user_id=user.id)
	category = CategoryFactory.build()
	product = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.MODERATED,
	)
	skus = [SkuFactory.build(product_id=product.id) for _ in range(3)]
	skus[0].active_quantity = 0
	cart_items = [
		CartItemFactory.build(
			user_id=user.id, sku_id=sku.id, quantity=2, unit_price_at_add=sku.price
		)
		for sku in skus
	]
	order = OrderFactory.build(
		buyer_id=user.id,
		address_id=address.id,
		payment_method_id=payment_method.id,
	)
	order_items = [OrderItemFactory.build(order_id=order.id) for _ in range(3)]
	db_session.add_all(
		[
			user,
			address,
			payment_method,
			category,
			product,
			*skus,
			*cart_items,
			order,
			*order_items,
		]
	)
	await db_session.commit()
	return OrderData(
		order=order,
		order_items=order_items,
		address=address,
		payment_method=payment_method,
		cart_items=cart_items,
		skus=skus,
		product=product,
	)


@pytest.fixture()
async def assembling_order_data(db_session: AsyncSession) -> OrderData:
	user = UserFactory.build()
	address = AddressFactory.build(user_id=user.id)
	payment_method = PaymentMethodFactory.build(user_id=user.id)
	category = CategoryFactory.build()
	product = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.MODERATED,
	)
	skus = [SkuFactory.build(product_id=product.id) for _ in range(3)]
	order = OrderFactory.build(
		buyer_id=user.id,
		address_id=address.id,
		payment_method_id=payment_method.id,
		status=OrderStatusEnum.ASSEMBLING,
	)
	order_items = [
		OrderItemFactory.build(order_id=order.id, sku_id=sku.id, unit_price=sku.price)
		for sku in skus
	]
	order_status_history = OrderStatusHistoryFactory.build(
		order_id=order.id, status=OrderStatusEnum.ASSEMBLING
	)
	db_session.add_all(
		[
			user,
			address,
			payment_method,
			category,
			product,
			*skus,
			order,
			*order_items,
			order_status_history,
		]
	)
	await db_session.commit()
	return OrderData(
		order=order,
		order_items=order_items,
		address=address,
		payment_method=payment_method,
		skus=skus,
		product=product,
		cart_items=[],
	)


@pytest.fixture()
async def delivering_order_data(db_session: AsyncSession) -> OrderData:
	user = UserFactory.build()
	address = AddressFactory.build(user_id=user.id)
	payment_method = PaymentMethodFactory.build(user_id=user.id)
	category = CategoryFactory.build()
	product = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.MODERATED,
	)
	skus = [SkuFactory.build(product_id=product.id) for _ in range(3)]
	order = OrderFactory.build(
		buyer_id=user.id,
		address_id=address.id,
		payment_method_id=payment_method.id,
		status=OrderStatusEnum.DELIVERING,
	)
	order_items = [
		OrderItemFactory.build(order_id=order.id, sku_id=sku.id, unit_price=sku.price)
		for sku in skus
	]
	order_status_history = OrderStatusHistoryFactory.build(
		order_id=order.id, status=OrderStatusEnum.DELIVERING
	)
	db_session.add_all(
		[
			user,
			address,
			payment_method,
			category,
			product,
			*skus,
			order,
			*order_items,
			order_status_history,
		]
	)
	await db_session.commit()
	return OrderData(
		order=order,
		order_items=order_items,
		address=address,
		payment_method=payment_method,
		skus=skus,
		product=product,
		cart_items=[],
	)


@pytest.fixture()
async def delivered_order_data(db_session: AsyncSession) -> OrderData:
	user = UserFactory.build()
	address = AddressFactory.build(user_id=user.id)
	payment_method = PaymentMethodFactory.build(user_id=user.id)
	category = CategoryFactory.build()
	product = ProductFactory.build(
		category_id=category.id,
		status=ProductStatusEnum.MODERATED,
	)
	skus = [SkuFactory.build(product_id=product.id) for _ in range(3)]
	order = OrderFactory.build(
		buyer_id=user.id,
		address_id=address.id,
		payment_method_id=payment_method.id,
		status=OrderStatusEnum.DELIVERED,
	)
	order_items = [
		OrderItemFactory.build(order_id=order.id, sku_id=sku.id, unit_price=sku.price)
		for sku in skus
	]
	order_status_history = OrderStatusHistoryFactory.build(
		order_id=order.id, status=OrderStatusEnum.DELIVERED
	)
	db_session.add_all(
		[
			user,
			address,
			payment_method,
			category,
			product,
			*skus,
			order,
			*order_items,
			order_status_history,
		]
	)
	await db_session.commit()
	return OrderData(
		order=order,
		order_items=order_items,
		address=address,
		payment_method=payment_method,
		skus=skus,
		product=product,
		cart_items=[],
	)
