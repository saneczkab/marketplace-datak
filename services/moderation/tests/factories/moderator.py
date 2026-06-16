import uuid

import factory

from database.models.identity.moderator import Moderator, ModeratorRole
from core.security import get_password_hash


class ModeratorFactory(factory.Factory):
	class Meta:
		model = Moderator

	id = factory.LazyFunction(uuid.uuid4)
	email = factory.Sequence(lambda n: f"moderator{n}@example.com")
	password_hash = factory.LazyFunction(lambda: get_password_hash("password12345"))
	first_name = "Test"
	last_name = "Moderator"
	role = ModeratorRole.MODERATOR
	is_active = True
	category_specializations = None
