import fastapi
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from services import auth_service
from core import db
from schemas.user import LoginResponse, RegisterRequest, LoginRequest, SessionInfo

router = fastapi.APIRouter(prefix="/api/v1/auth", tags=["Авторизация"])
security = HTTPBearer()


@router.post("/register")
async def register(
	data: RegisterRequest,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> LoginResponse:
	try:
		return await auth_service.register(data, db)
	except Exception as e:  # noqa
		raise fastapi.HTTPException(status_code=404, detail=f"{e}") from e


@router.post("/login")
async def login(
	data: LoginRequest,
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
) -> LoginResponse:
	try:
		return await auth_service.login(data, db)
	except Exception as e:  # noqa
		raise fastapi.HTTPException(status_code=404, detail=f"{e}") from e


@router.get("/me")
async def get_session_info(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	credentials: HTTPAuthorizationCredentials = fastapi.Depends(security),  # noqa
) -> SessionInfo:
	token = credentials.credentials
	try:
		return await auth_service.get_session_info(token, db)
	except Exception as e:
		raise fastapi.HTTPException(status_code=417, detail=f"{e}") from e


@router.post("/logout")
async def logout(
	db: Annotated[AsyncSession, fastapi.Depends(db.get_db)],
	credentials: HTTPAuthorizationCredentials = fastapi.Depends(security),  # noqa
) -> None:
	token = credentials.credentials
	try:
		await auth_service.logout(token, db)
	except Exception as e:
		raise fastapi.HTTPException(status_code=418, detail=f"{e}") from e
