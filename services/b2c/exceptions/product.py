class ProductError(Exception):
	"""Base exception for product-related errors."""


class ProductNotFoundError(ProductError):
	"""Raised when a product is not found."""


class InvalidSortError(Exception):
	"""An exception is thrown if an invalid sort parameter is passed."""


class InvalidSearchQueryError(Exception):
	"""An exception is thrown if the search query 'q' is too short or too long."""


class InvalidFilterError(Exception):
	"""An exception is thrown if the filter parameters are invalid or corrupted."""
