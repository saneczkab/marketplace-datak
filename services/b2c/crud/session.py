from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
import datetime


from database.models import Session
from core.config import settings

import uuid


async def create_session(
	user_id: uuid.UUID, access_token: str, refresh_token: str, db: AsyncSession
) -> None:
	await db.execute(
		insert(Session).values(
			user_id=user_id,
			access_token=access_token,
			refresh_token=refresh_token,
			expires_at=datetime.datetime.now(datetime.timezone.utc)
			+ datetime.timedelta(seconds=settings.SESSION_EXPIRE_SECONDS),
		)
	)
