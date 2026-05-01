from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	database_url: str
	debug: bool = False

	model_config = SettingsConfigDict(
		extra="ignore",
	)


settings = Settings()
