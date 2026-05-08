from sqlalchemy.ext.asyncio import AsyncSession
import crud.user as user_crud
import hashlib

from schemas.user import LoginResponse

from database.models import User

from exceptions.user import UserAlreadyExistsError, UserPasswordTooWeakError


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

	password_hash = hashlib.sha256(password.encode()).hexdigest()

	user: User = User(username=username, email=email, password_hash=password_hash)
	await user_crud.create_user(user, db)

	# TODO: Generate and return access token
	return LoginResponse(
		access_token="access_token",  # noqa
		refresh_token="refresh_token",  # noqa
		expires_in=3600,
		token_type="bearer",  # noqa
	)


async def password_difficulty(password: str) -> bool:
	return len(password) >= 3
