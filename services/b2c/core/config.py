from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	DATABASE_URL: str
	DEBUG: bool = False
	DATABASE_VERBOSE: bool

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="allow",
		case_sensitive=False,  # Позволяет использовать database_url или DATABASE_URL
	)


settings = Settings()
