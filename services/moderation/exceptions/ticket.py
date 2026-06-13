class TicketError(Exception):
	"""Base exception for moderation ticket decision errors."""


class TicketNotFoundError(TicketError):
	"""No moderation ticket exists for the given id."""


class TicketNotAssignedError(TicketError):
	"""Ticket is assigned to another moderator."""


class TicketWrongStatusError(TicketError):
	"""Ticket is not in IN_REVIEW status."""


class TicketNoSkusError(TicketError):
	"""Product has no SKUs in the local catalog replica."""


class TicketHardBlockedError(TicketError):
	"""Ticket is in terminal HARD_BLOCKED status."""
