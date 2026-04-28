from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    USER_DB: str
    PASSWORD_DB: str
    HOST_DB: str
    PORT_DB: int
    NAME_DB: str

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.USER_DB}:{self.PASSWORD_DB}@{self.HOST_DB}:{self.PORT_DB}/{self.NAME_DB}"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra="ignore",
    )

settings = Settings()