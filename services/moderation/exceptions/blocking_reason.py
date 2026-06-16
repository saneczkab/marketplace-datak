class BlockingReasonError(Exception):
	"""Base exception for blocking reason errors."""


class BlockingReasonNotFoundError(BlockingReasonError):
	"""Blocking reason does not exist."""


class BlockingReasonCodeExistsError(BlockingReasonError):
	"""Blocking reason code is already in use."""
