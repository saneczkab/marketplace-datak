import factory
import uuid

from database.models.catalog.inventory import Invoice, InvoiceStatusEnum
from datetime import datetime


class InvoiceFactory(factory.Factory):
	class Meta:
		model = Invoice

	id = factory.LazyFunction(uuid.uuid4)
	seller_id = factory.LazyFunction(uuid.uuid4)
	status = InvoiceStatusEnum.CREATED
	created_at = factory.LazyFunction(datetime.now)
	updated_at = factory.LazyFunction(datetime.now)
	accepted_at = factory.LazyFunction(datetime.now)
	items = factory.LazyFunction(list)
