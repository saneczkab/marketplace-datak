class InvoiceError(Exception):
	"""Basic exception for invoices"""


class InvoiceNotFoundError(InvoiceError):
	"""Basic exception when an invoice is not found in the database."""


class InvalidInvoiceStatusError(InvoiceError):
	"""Basic exception when attempting to perform an action that is not available for the current status."""


class EmptyInvoiceError(InvoiceError):
	"""Basic exception if there are no items in the invoice"""


class InvoiceOwnershipError(InvoiceError):
	"""Raised when one or more SKUs do not belong to the authenticated seller."""


class SkuNotModeratedError(InvoiceError):
	"""Raised when trying to create invoice with non-moderated SKU."""


class InvalidQuantityError(InvoiceError):
	"""Raised when quantity is not valid (e.g., <= 0)."""
