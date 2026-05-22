from pydantic_settings import BaseSettings


class settings(BaseSettings):  # noqa
	DATABASE_URL: str

	SESSION_EXPIRE_SECONDS: int
	SECRET_KEY: str
	ALGORITHM: str

	S3_ENDPOINT: str
	S3_ACCESS_KEY: str
	S3_SECRET_KEY: str
	S3_BUCKET: str
	MAX_SIZE: int

	model_config = {"env_file": ".env", "extra": "allow"}


settings = settings()
