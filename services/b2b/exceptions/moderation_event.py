class ModerationEventError(Exception):
	"""Base exception for moderation event processing."""


class ModerationEventValidationError(ModerationEventError):
	"""Raised when moderation event payload is invalid."""


class ModerationEventDuplicateError(ModerationEventError):
	"""Raised when the same event was already processed (idempotent no-op)."""
