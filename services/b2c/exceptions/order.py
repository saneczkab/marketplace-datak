class OrderError(Exception):
	"""Base exception for order operations"""

	pass


class IdempotencyConflictError(OrderError):
	"""Idempotency conflict error"""

	pass


class InvalidIdempotencyKeyError(OrderError):
	"""Invalid idempotency key error"""

	pass


class ReserveFailedError(OrderError):
	"""Reserve failed error"""

	def __init__(self, failed_items: list[dict]) -> None:
		self.failed_items = failed_items
		super().__init__(failed_items)


class B2BUnavailableError(OrderError):
	"""B2B unavailable error"""

	pass


class AddressNotFoundError(OrderError):
	"""Address not found error"""

	pass


class PaymentMethodNotFoundError(OrderError):
	"""Payment method not found error"""

	pass


class EmptyCartError(OrderError):
	"""Empty cart error"""

	pass


class OrderNotFoundError(OrderError):
	"""Order not found error"""

	pass


class OrderNotCancelableError(OrderError):
	"""Order not cancelable error (not created or paid)"""

	pass
