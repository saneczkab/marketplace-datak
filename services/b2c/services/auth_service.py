from sqlalchemy.ext.asyncio import AsyncSession
import crud.user as user_crud
import crud.session as session_crud
import uuid
import secrets

from schemas.user import LoginRequest, LoginResponse, RegisterRequest, SessionData

from database.models import User

from exceptions.user import (
	UserAlreadyExistsError,
	UserInvalidPasswordError,
	UserNotFoundError,
	UserPasswordTooWeakError,
	UserLoginConflictError,
)

from core.config import settings

import core.security as security


async def register(
	data: RegisterRequest,
	db: AsyncSession,
) -> LoginResponse:
	# check if username or email already exists
	existing_user = await user_crud.get_user_by_username(data.username, db)
	if existing_user:
		raise UserAlreadyExistsError(
			f"User with username '{data.username}' already exists."
		)

	existing_user = await user_crud.get_user_by_email(data.email, db)
	if existing_user:
		raise UserAlreadyExistsError(f"User with email '{data.email}' already exists.")

	if not await password_difficulty(data.password):
		raise UserPasswordTooWeakError(
			"Password does not meet the required complexity."
		)

	password_hash = await security.get_password_hash(data.password)

	user: User = User(
		username=data.username, email=data.email, password_hash=password_hash
	)
	await user_crud.create_user(user, db)

	session: SessionData = await generate_session(user.id, db)

	return LoginResponse(
		access_token=session.token,
		refresh_token="refresh_token",  # noqa
		expires_in=settings.SESSION_EXPIRE_SECONDS,
		token_type="bearer",  # noqa
	)


async def password_difficulty(password: str) -> bool:
	return len(password) >= 8


async def generate_session(user_id: uuid.UUID, db: AsyncSession) -> SessionData:
	token = await security.create_access_token(user_id)

	refresh_token = secrets.token_urlsafe(32)

	
	await session_crud.create_session(user_id, token, refresh_token, db)

	return SessionData(
		token=token,
		refresh_token=refresh_token,
		expires_in=settings.SESSION_EXPIRE_SECONDS,
		token_type="Bearer",  # noqa
	)


async def refresh_session() -> None:
	pass


async def login(data: LoginRequest, db: AsyncSession) -> LoginResponse:
	if data.email and data.username:
		raise UserLoginConflictError(
			"Both email and username provided for login, which is not allowed."
		)

	if not data.email and not data.username:
		raise UserLoginConflictError(
			"Neither email nor username provided for login, one is required."
		)

	user = None

	if data.email:
		user: User | None = await user_crud.get_user_by_email(data.email, db)
	else:
		user: User | None = await user_crud.get_user_by_username(data.username, db)

	if not user:
		raise UserNotFoundError("User not found with the provided credentials.")

	if not await security.verify_password(data.password, user.password_hash):
		raise UserInvalidPasswordError("Incorrect password provided.")

	session: SessionData = await generate_session(user.id, db)

	return LoginResponse(
		access_token=session.access_token,
		refresh_token=session.refresh_token,
		expires_in=session.expires_in,
		token_type="Bearer",  # noqa
	)
