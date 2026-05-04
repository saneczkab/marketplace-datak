import uuid

import factory

from database.models.catalog.base import (
	Category,
	CategoryFilters,
	FilterTypeEnum,
	FilterValues,
	Product,
	ProductStatusEnum,
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
