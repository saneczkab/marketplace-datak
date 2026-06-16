from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.blocking_reason import BlockingReason


async def get_active_by_ids(
	db: AsyncSession, reason_ids: list[UUID]
) -> list[BlockingReason]:
	if not reason_ids:
		return []
	result = await db.execute(
		select(BlockingReason).where(
			BlockingReason.id.in_(reason_ids),
			BlockingReason.is_active.is_(True),
		)
	)
	reasons = list(result.scalars().all())
	reason_map = {reason.id: reason for reason in reasons}
	return [
		reason_map[reason_id] for reason_id in reason_ids if reason_id in reason_map
	]
