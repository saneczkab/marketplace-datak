import uuid

import factory

from database.models import Sku
from database.models.cart.item import CartItem
from database.models.catalog.base import (
	Category,
	CategoryFilters,
	FilterTypeEnum,
	FilterValues,
	Product,
	ProductStatusEnum,
	Review,
)


class CategoryFactory(factory.Factory):
	class Meta:
		model = Category

	id = factory.LazyFunction(uuid.uuid4)
	parent_id = None
	name = factory.Faker("sentence", nb_words=2)
	slug = factory.Faker("slug")
	description = None
	is_active = True
	seo = None
	image_url = None


class CategoryFiltersFactory(factory.Factory):
	class Meta:
		model = CategoryFilters

	id = factory.LazyFunction(uuid.uuid4)
	category_id = factory.LazyFunction(uuid.uuid4)
	name = factory.Faker("sentence", nb_words=2)
	slug = factory.Faker("slug")
	type = FilterTypeEnum.LIST
	value = factory.Faker("word")
	min = None
	max = None


class FilterValuesFactory(factory.Factory):
	class Meta:
		model = FilterValues

	id = factory.LazyFunction(uuid.uuid4)
	filter_id = factory.LazyFunction(uuid.uuid4)
	value = factory.Faker("word")


class ProductFactory(factory.Factory):
	class Meta:
		model = Product

	id = factory.LazyFunction(uuid.uuid4)
	seller_id = factory.LazyFunction(uuid.uuid4)
	category_id = factory.LazyFunction(uuid.uuid4)
	title = factory.Faker("sentence", nb_words=3)
	slug = factory.Faker("slug")
	description = factory.Faker("sentence", nb_words=6)
	status = ProductStatusEnum.MODERATED


class SkuFactory(factory.Factory):
	class Meta:
		model = Sku

	id = factory.LazyFunction(uuid.uuid4)
	product_id = factory.LazyFunction(uuid.uuid4)
	name = factory.Faker("sentence", nb_words=2)
	price = factory.Faker("pyint", min_value=100, max_value=10000)
	active_quantity = factory.Faker("pyint", min_value=0, max_value=100)


class ReviewFactory(factory.Factory):
	class Meta:
		model = Review

	id = factory.LazyFunction(uuid.uuid4)
	product_id = factory.LazyFunction(uuid.uuid4)
	user_id = factory.LazyFunction(uuid.uuid4)
	rating = factory.Faker("pyint", min_value=1, max_value=5)
	comment = factory.Faker("sentence", nb_words=8)


class CartItemFactory(factory.Factory):
	class Meta:
		model = CartItem

	id = factory.LazyFunction(uuid.uuid4)
	user_id = factory.LazyFunction(uuid.uuid4)
	sku_id = factory.LazyFunction(uuid.uuid4)
	quantity = factory.Faker("pyint", min_value=1, max_value=10)
