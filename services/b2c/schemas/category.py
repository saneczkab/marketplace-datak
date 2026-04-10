import uuid

from pydantic import BaseModel


class Parent(BaseModel):
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


class GetCategoryResponse(BaseModel):
	id: uuid.UUID
	name: str
	slug: str
	description: str | None
	parent: Parent | None
	product_count: int
	seo: Seo | None
	meta: CategoryMeta | None
	image_url: str | None
	is_active: bool
	created_at: str
	updated_at: str

