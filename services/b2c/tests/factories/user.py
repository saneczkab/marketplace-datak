from database.models.identity.user import User
import factory
import uuid
from datetime import datetime


class UserFactory(factory.Factory):
	class Meta:
		model = User

	id = factory.LazyFunction(uuid.uuid4)
	username = factory.Sequence(lambda n: f"user_{n}")
	email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
	password_hash = factory.Faker("password")
	created_at = factory.LazyFunction(datetime.now)
