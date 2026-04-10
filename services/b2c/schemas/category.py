import uuid

from pydantic import BaseModel


class CategoryParent(BaseModel):
	id: uuid.UUID
	name: str
	slug: str


class Seo(BaseModel):
	title: str
	description: str
	keywords: list[str]


class CategoryMeta(BaseModel):
	og_title: str | None
	og_description: str | None
	og_image: str | None
	twitter_card: str | None


class CategoryInfoResponse(BaseModel):
	id: uuid.UUID
	name: str
	slug: str
	description: str | None
	parent: CategoryParent | None
	product_count: int
	seo: Seo | None
	meta: CategoryMeta | None
	image_url: str | None
	is_active: bool
	created_at: str
	updated_at: str

# Tree response models

class CategoryTreeResponse(BaseModel):
	items: list[CategoryNode]

class CategoryNode(BaseModel):
	id: uuid.UUID
	name: str
	parent_id: uuid.UUID | None
	children: list[CategoryNode]