class UserError(Exception):
	"""Base exception for user-related errors."""


class UserAlreadyExistsError(UserError):
	"""Raised when a user with the given username or email already exists."""


class UserPasswordTooWeakError(UserError):
	"""Raised when the provided password does not meet the required complexity."""
