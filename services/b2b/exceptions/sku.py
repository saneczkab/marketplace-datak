from exceptions.base import MarketplaceError


class SkuError(MarketplaceError):
	"""Base exception for SKU-related errors."""


class SkuNotFoundError(SkuError):
	"""Raised when a SKU is not found in the catalog."""


class SkuAlreadyExistsError(SkuError):
	"""Raised when a SKU with the same attributes already exists."""
