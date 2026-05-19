import fastapi
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from exceptions.seller import (
	InvalidPasswordError,
	SellerAlreadyExistsError,
	SellerNotFoundError,
)
from schemas.auth import LoginRequest, SellerCreate, TokenResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core import db
from typing import Annotated
from services import auth_service


router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/register")
async def register(
	data: SellerCreate, db: Annotated[AsyncSession, fastapi.Depends(db.get_db)]
) -> TokenResponse:
	try:
		return await auth_service.register(data, db)
	except ValidationError as e:
		raise HTTPException(status_code=422, detail=f"{e}") from e
	except SellerAlreadyExistsError as e:
		raise HTTPException(status_code=409, detail="User already exists") from e


@router.post("/login")
async def login(data: LoginRequest) -> TokenResponse:
	try:
		return await auth_service.login(data, db)
	except ValidationError as e:
		raise HTTPException(status_code=422, detail=f"{e}") from e
	except SellerNotFoundError as e:
		raise HTTPException(status_code=401, detail="Invalid login") from e
	except InvalidPasswordError as e:
		raise HTTPException(status_code=401, detail="Invalid password") from e
