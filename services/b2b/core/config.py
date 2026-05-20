from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	DATABASE_URL: str

	SESSION_EXPIRE_SECONDS: int
	SECRET_KEY: str
	ALGORITHM: str

	model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()
