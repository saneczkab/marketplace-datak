import uuid
from typing import Annotated

from pydantic import BaseModel, StringConstraints, Field

CharacteristicName = Annotated[
	str,
	StringConstraints(strip_whitespace=True, min_length=1, pattern=r"^[A-Z_]+$"),
	Field(
		examples=["BRAND", "COLOR", "SIZE"],
	),
]


class Characteristic(BaseModel):
	id: uuid.UUID
	name: CharacteristicName
	value: str
