from fastapi import HTTPException, status


class CategoryError(HTTPException):
	def __init__(self, detail: str) -> None:
		super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class CategoryNotFoundError(CategoryError):
	def __init__(self, detail: str = "Category not found") -> None:
		super().__init__(detail=detail)
