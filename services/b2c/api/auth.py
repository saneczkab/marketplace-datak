import fastapi
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from services import auth_service
from core import db
from schemas.user import LoginResponse

router = fastapi.APIRouter(prefix="/api/v1/auth")


@router.post("/register")
async def register(
	username: str,
	email: str,
	password: str,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> LoginResponse:
	try:
		return await auth_service.register(username, email, password, db)
	except Exception as e:  # noqa
		pass
