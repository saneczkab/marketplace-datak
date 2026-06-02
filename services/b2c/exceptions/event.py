class EventError(Exception):
	"""Base event-related error"""


class EventDuplicatError(EventError):
	"""Raised when even was already issued"""
