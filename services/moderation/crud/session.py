from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity.moderator import Session


async def add_session(session: Session, db: AsyncSession) -> Session:
	db.add(session)
	await db.commit()
	await db.refresh(session)
	return session


async def check_active_session(token: str, db: AsyncSession) -> bool:
	result = await db.execute(select(Session).where(Session.access_token == token))
	session = result.scalar_one_or_none()
	if session is None:
		return False
	return session.is_active


async def get_session_by_access_token(
	access_token: str, db: AsyncSession
) -> Session | None:
	result = await db.execute(
		select(Session).where(Session.access_token == access_token)
	)
	return result.scalar_one_or_none()
