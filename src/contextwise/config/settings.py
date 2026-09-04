from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "contextwise"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
