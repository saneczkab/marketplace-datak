from database.models import Session
from sqlalchemy.ext.asyncio import AsyncSession


async def add_session(session: Session, db: AsyncSession) -> Session:
	db.add(session)
	await db.commit()
	await db.refresh(session)
	return session
