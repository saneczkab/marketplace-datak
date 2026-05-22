from sqlalchemy.ext.asyncio import AsyncSession
from schemas.banner import Banner
import crud.banner as banner_crud


async def get_active_banners(db: AsyncSession) -> list[Banner]:
	banners = await banner_crud.get_active_banners(db)
	return [
		Banner(
			id=banner.id,
			title=banner.title,
			image_url=banner.image_url,
			link=banner.link,
			ordering=banner.priority,
			active_from=banner.start_at,
			active_to=banner.end_at,
		)
		for banner in banners
	]
