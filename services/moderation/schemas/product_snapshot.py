from uuid import UUID

from pydantic import BaseModel, Field


class ProductSnapshotCategory(BaseModel):
	id: UUID
	name: str


class ProductSnapshotImage(BaseModel):
	id: UUID
	url: str
	ordering: int = 0


class ProductSnapshotCharacteristic(BaseModel):
	id: UUID
	name: str
	value: str


class ProductSnapshotSku(BaseModel):
	id: UUID
	product_id: UUID
	name: str
	price: int
	discount: int = 0
	active_quantity: int = 0
	article: str | None = None
	image: str | None = None
	images: list[ProductSnapshotImage] = Field(default_factory=list)
	characteristics: list[ProductSnapshotCharacteristic] = Field(default_factory=list)


class ProductSnapshot(BaseModel):
	id: UUID
	seller_id: UUID
	category_id: UUID
	title: str
	slug: str
	description: str = ""
	status: str
	deleted: bool = False
	blocked: bool = False
	category: ProductSnapshotCategory
	images: list[ProductSnapshotImage] = Field(default_factory=list)
	characteristics: list[ProductSnapshotCharacteristic] = Field(default_factory=list)
	skus: list[ProductSnapshotSku] = Field(default_factory=list)
	blocking_reason: str | None = None
	field_reports: list[dict[str, str]] = Field(default_factory=list)
