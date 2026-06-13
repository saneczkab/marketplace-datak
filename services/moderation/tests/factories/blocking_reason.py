import uuid

import factory

from database.models.blocking_reason import BlockingReason


class BlockingReasonFactory(factory.Factory):
	class Meta:
		model = BlockingReason

	id = factory.LazyFunction(uuid.uuid4)
	code = factory.Sequence(lambda n: f"TEST_REASON_{n}")
	title = "Test blocking reason"
	description = None
	hard_block = False
	is_active = True

	class Params:
		hard = factory.Trait(
			hard_block=True,
			title="Hard block test reason",
		)
