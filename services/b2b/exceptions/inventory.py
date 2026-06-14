class InventoryError(Exception):
	"""Base inventory operation error."""


class InventoryValidationError(InventoryError):
	"""Invalid reserve/unreserve request."""


class ReserveConflictError(InventoryError):
	def __init__(self, failed_items: list[dict]) -> None:
		self.failed_items = failed_items
		super().__init__("Insufficient stock for one or more SKUs")


class UnreserveConflictError(InventoryError):
	"""Reserved quantity is less than requested unreserve amount."""


class FulfillConflictError(InventoryError):
	"""Reserved quantity is less than the requested fulfill amount."""
