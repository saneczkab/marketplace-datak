class CartError(Exception):
	"""Base exception for cart operations"""

	pass


class MissingCartIdentityError(CartError):
	"""Raised when neither X-User-Id nor X-Session-Id is provided"""

	pass


class BothIdentitiesProvidedError(CartError):
	"""Raised when both X-User-Id and X-Session-Id are provided"""

	pass


class CartItemNotFoundError(CartError):
	"""Raised when cart item is not found"""

	pass
