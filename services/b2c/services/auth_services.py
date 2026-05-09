from sqlalchemy.ext.asyncio import AsyncSession
import crud.user as user_crud
import hashlib
import uuid

from schemas.user import LoginResponse, RegisterRequest, SessionData

from database.models import User

from exceptions.user import UserAlreadyExistsError, UserPasswordTooWeakError

from core.config import settings

import core.security as security

async def register(
	username: str,
	email: str,
	password: str,
	db: AsyncSession,
) -> LoginResponse:
	# check if username or email already exists
	existing_user = await user_crud.get_user_by_username(username, db)
	if existing_user:
		raise UserAlreadyExistsError(f"User with username '{username}' already exists.")

	existing_user = await user_crud.get_user_by_email(email, db)
	if existing_user:
		raise UserAlreadyExistsError(f"User with email '{email}' already exists.")

	if not await password_difficulty(password):
		raise UserPasswordTooWeakError(
			"Password does not meet the required complexity."
		)

	RegisterRequest(username=username, email=email, password=password).model_validate()

	password_hash = await security.get_password_hash(password)

	user: User = User(username=username, email=email, password_hash=password_hash)
	await user_crud.create_user(user, db)

	# TODO: Generate and return access token
	return LoginResponse(
		access_token=await security.create_access_token(user.id),  
		refresh_token="refresh_token",  # noqa
		expires_in=settings.SESSION_EXPIRE_SECONDS,
		token_type="bearer",  # noqa
	)


async def password_difficulty(password: str) -> bool:
	return len(password) >= 3


async def generate_session(user_id: uuid.UUID) -> SessionData:
	pass


async def refresh_session():
	pass
