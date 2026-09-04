from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "contextwise"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    llm_primary_model: str = "fake-default"
    llm_fallback_model: str | None = None
    llm_timeout_seconds: float = Field(default=30, gt=0)
    llm_max_retries: int = Field(default=1, ge=0, le=3)
    llm_structured_repair_attempts: int = Field(default=1, ge=0, le=2)
    llm_models_json: str | None = None
