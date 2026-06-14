from pydantic_settings import BaseSettings


class settings(BaseSettings):  # noqa
	DATABASE_URL: str

	SESSION_EXPIRE_SECONDS: int
	SECRET_KEY: str
	ALGORITHM: str

	RABBITMQ_HOST: str
	RABBITMQ_PORT: str
	RABBITMQ_USER: str
	RABBITMQ_PASSWORD: str
	RABBITMQ_EXCHANGE: str

	B2B_SERVICE_KEY: str = ""
	OUTBOX_POLL_INTERVAL_SECONDS: int = 5
	IN_REVIEW_CLAIM_TIMEOUT_MINUTES: int = 30

	model_config = {"env_file": ".env", "extra": "allow"}


settings = settings()
