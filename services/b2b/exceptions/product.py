from exceptions.base import MarketplaceError


class ProductError(MarketplaceError):
	"""Base exception for product-related errors."""


class ProductNotFoundError(ProductError):
	"""Raised when a product is not found in the catalog."""


class ProductNotOwnerError(ProductError):
	"""Raised when the product belongs to another seller."""
