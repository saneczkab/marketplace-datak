import fastapi
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from services import auth_service
from core import db
from schemas.user import LoginResponse, RegisterRequest

router = fastapi.APIRouter(prefix="/api/v1/auth", tags=["Авторизация"])


@router.post("/register")
async def register(
	data: RegisterRequest,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> LoginResponse:
	try:
		return await auth_service.register(data, db)
	except Exception as e:  # noqa
		raise fastapi.HTTPException(status_code=404, detail=f"{e}") from e
