import factory
import uuid
from datetime import datetime
from database.models.personal.profile import Favorite, Subscription


class FavoriteFactory(factory.Factory):
	class Meta:
		model = Favorite

	user_id = factory.LazyFunction(uuid.uuid4)
	product_id = factory.LazyFunction(uuid.uuid4)
	added_at = factory.LazyFunction(datetime.now)


class SubscriptionFactory(factory.Factory):
	class Meta:
		model = Subscription

	user_id = factory.LazyFunction(uuid.uuid4)
	product_id = factory.LazyFunction(uuid.uuid4)
	notify_in_stock = factory.LazyFunction(bool)
	notify_price_down = factory.LazyFunction(bool)
	created_at = factory.LazyFunction(datetime.now)
