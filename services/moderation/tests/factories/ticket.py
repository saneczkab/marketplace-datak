import uuid

import factory

from database.models.tickets.ticket import Ticket, TicketKind, TicketStatus


class TicketFactory(factory.Factory):
	class Meta:
		model = Ticket

	id = factory.LazyFunction(uuid.uuid4)
	product_id = factory.LazyFunction(uuid.uuid4)
	seller_id = factory.LazyFunction(uuid.uuid4)
	category_id = factory.LazyFunction(uuid.uuid4)
	kind = TicketKind.CREATE
	status = TicketStatus.PENDING
	queue_priority = 1
	total_active_quantity = 0
	json_before = None
	json_after = factory.LazyAttribute(
		lambda obj: {
			"id": str(obj.product_id),
			"seller_id": str(obj.seller_id),
			"title": "Original title",
			"description": "Original description",
			"status": "ON_MODERATION",
			"deleted": False,
			"skus": [],
		}
	)
	assigned_moderator_id = None
