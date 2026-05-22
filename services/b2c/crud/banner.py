from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.storefront.main import Banner


async def get_active_banners(db: AsyncSession) -> list[Banner]:
	current_date = datetime.now()
	query = select(Banner).where(
		Banner.is_active == True,  # noqa
		Banner.start_at <= current_date,
		Banner.end_at >= current_date,
	)
	result = await db.execute(query)
	return result.scalars().all()
