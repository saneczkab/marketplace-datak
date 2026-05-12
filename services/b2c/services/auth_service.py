from sqlalchemy.ext.asyncio import AsyncSession
import crud.user as user_crud
import uuid

from schemas.user import LoginResponse, RegisterRequest, SessionData

from database.models import User

from exceptions.user import UserAlreadyExistsError, UserPasswordTooWeakError

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
	token = await security.create_access_token(user.id)
	# TODO: Generate and return access token # noqa
	return LoginResponse(
		access_token=token,
		refresh_token="refresh_token",  # noqa
		expires_in=settings.SESSION_EXPIRE_SECONDS,
		token_type="bearer",  # noqa
	)


async def password_difficulty(password: str) -> bool:
	return len(password) >= 3


async def generate_session(user_id: uuid.UUID) -> SessionData:
	pass


async def refresh_session() -> None:
	pass
