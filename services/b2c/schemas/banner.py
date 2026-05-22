from datetime import datetime
import uuid

from pydantic import BaseModel


class Banner(BaseModel):
	id: uuid.UUID
	title: str
	image_url: str
	link: str
	ordering: int
	active_from: datetime
	active_to: datetime
