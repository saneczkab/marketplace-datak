from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	DATABASE_URL: str
	DEBUG: bool = False
	DATABASE_VERBOSE: bool

	SESSION_EXPIRE_SECONDS: int

	SECRET_KEY: str
	ALGORITHM: str

	X_SERVICE_KEY: str

	RABBITMQ_URL: str = "None"
	RABBITMQ_EXCHANGE: str = "None"

	INBOX_MESSAGES_PROCESSING_DELAY: int
	OUTBOX_MESSAGES_PROCESSING_DELAY: int

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="allow",
		case_sensitive=False,  # Позволяет использовать database_url или DATABASE_URL
	)


settings = Settings()
