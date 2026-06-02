class ProductError(Exception):
	"""Base exception for product-related errors."""


class ProductNotFoundError(ProductError):
	"""Raised when a product is not found."""


class InvalidFiltersError(ProductError):
	"""Raised when the filters parameter contains invalid JSON."""


class SearchQueryTooShortError(ProductError):
	"""Raised when the search query is shorter than the minimum allowed length."""
