class B2BServiceUnavailableError(Exception):
	"""Исключение выбрасывается, если B2B-сервис лежит или вернул 5xx ошибку"""

	pass


class B2BNotFoundError(Exception):
	"""Исключение выбрасывается, если B2B вернул 404 (категория не найдена)"""

	pass
