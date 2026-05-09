from passlib.context import CryptContext
from .config import Settings
import uuid
import datetime
from jose import jwt

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


async def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


async def create_access_token(user_id: uuid.UUID) -> str:
    # gonna encrypt user_id and expires_at 
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=Settings.ACCESS_TOKEN_EXPIRE_SECONDS)

    data = {
        "user_id": str(user_id),
        "expires_at": expires_at.isoformat()
    }
	
    encode_jwt = jwt.encode(data, Settings.SECRET_KEY, algorithm=Settings.ALGORITHM)
    return encode_jwt

async def decode_access_token(token: str) -> dict:
	return jwt.decode(token, Settings.SECRET_KEY, algorithms=[Settings.ALGORITHM])