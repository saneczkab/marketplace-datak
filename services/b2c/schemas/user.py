from pydantic import BaseModel, EmailStr
import datetime
import uuid


class LoginResponse(BaseModel):
	access_token: str
	refresh_token: str
	expires_in: int
	token_type: str


class RegisterRequest(BaseModel):
	username: str
	email: EmailStr
	password: str


class SessionData(BaseModel):
	session_id: uuid.UUID
	user_id: uuid.UUID
	token: str
	refresh_token: str
	issued_at: datetime.datetime
	expires_in: int

