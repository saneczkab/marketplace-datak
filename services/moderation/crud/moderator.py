from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity.moderator import Moderator


async def get_by_id(db: AsyncSession, moderator_id: UUID) -> Moderator | None:
	result = await db.execute(select(Moderator).where(Moderator.id == moderator_id))
	return result.scalar_one_or_none()
