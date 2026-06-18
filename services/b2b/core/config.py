from pydantic_settings import BaseSettings


class settings(BaseSettings):  # noqa
	DATABASE_URL: str
	DATABASE_VERBOSE: bool

	SESSION_EXPIRE_SECONDS: int
	SECRET_KEY: str
	ALGORITHM: str

	S3_ENDPOINT: str
	S3_ACCESS_KEY: str
	S3_SECRET_KEY: str
	S3_BUCKET: str
	MAX_SIZE: int

	RABBITMQ_URL: str = "None"
	RABBITMQ_EXCHANGE: str = "None"

	INBOX_MESSAGES_PROCESSING_DELAY: int = 1
	OUTBOX_MESSAGES_PROCESSING_DELAY: int = 1

	B2C_SERVICE_KEY: str = ""
	MODERATION_SERVICE_KEY: str = ""

	model_config = {"env_file": ".env", "extra": "allow"}


settings = settings()
