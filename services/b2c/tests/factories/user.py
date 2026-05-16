from database.models.identity.user import User
import factory
import uuid
from datetime import datetime


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    created_at = factory.LazyFunction(datetime.now)
