class B2BEventError(Exception):
	"""Base exception for incoming B2B event processing errors."""


class B2BEventValidationError(B2BEventError):
	"""Invalid B2B event payload or business rule violation."""


class TicketAlreadyExistsError(B2BEventError):
	"""Ticket for product already exists (duplicate CREATED)."""


class TicketNotFoundError(B2BEventError):
	"""No moderation ticket exists for the product."""
