from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Image


async def add_image(image: Image, db: AsyncSession) -> Image:
	db.add(image)
	await db.commit()
	await db.refresh(image)
	return image
