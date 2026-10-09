from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

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
    owner_token: str = Field(
        default="local-development-token", alias="CONTEXTWISE_OWNER_TOKEN", min_length=1
    )
    owner_id: str = Field(default="local", alias="CONTEXTWISE_OWNER_ID", min_length=1)
    context_budget: int = Field(default=4096, alias="CONTEXTWISE_CONTEXT_BUDGET", gt=0)
    output_reserve: int = Field(default=512, alias="CONTEXTWISE_OUTPUT_RESERVE", ge=0)
    title_model: str | None = Field(default=None, alias="LLM_TITLE_MODEL")
    document_store_path: str = Field(
        default="./data/documents", alias="CONTEXTWISE_DOCUMENT_STORE_PATH"
    )
    document_max_bytes: int = Field(
        default=10_485_760, alias="CONTEXTWISE_DOCUMENT_MAX_BYTES", gt=0
    )
    ingestion_timeout_seconds: float = Field(
        default=30, alias="CONTEXTWISE_INGESTION_TIMEOUT_SECONDS", gt=0
    )
    embedding_model: str = Field(default="hash-256-v1", alias="CONTEXTWISE_EMBEDDING_MODEL")
    embedding_api_key: str | None = Field(default=None, alias="CONTEXTWISE_EMBEDDING_API_KEY")
    embedding_base_url: str = Field(
        default="https://api.openai.com/v1", alias="CONTEXTWISE_EMBEDDING_BASE_URL"
    )

    @model_validator(mode="after")
    def require_production_owner_token(self) -> "Settings":
        if self.environment == "production" and self.owner_token == "local-development-token":
            raise ValueError("production requires a non-default CONTEXTWISE_OWNER_TOKEN")
        return self
