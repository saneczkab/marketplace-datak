class CatalogError(Exception):
	"""Base exception for catalog replication errors."""


class CatalogEventValidationError(CatalogError):
	"""Invalid catalog replication event."""


class CatalogProductNotFoundError(CatalogError):
	"""Product is missing in the local catalog replica."""
