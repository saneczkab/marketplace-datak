from typing import List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Image
import uuid


async def add_image(image: Image, db: AsyncSession) -> Image:
	db.add(image)
	await db.commit()
	await db.refresh(image)
	return image


async def get_product_images_by_id(
	product_id: uuid.UUID, db: AsyncSession
) -> List[Image]:
	result = await db.execute(
		select(Image).where(
			and_(Image.entity_type == "PRODUCT", Image.entity_id == product_id)
		)
	)
	return result.fetchall()
