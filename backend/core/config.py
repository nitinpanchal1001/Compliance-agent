from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    secret_key: str = "change-me"
    debug: bool = False

    # Postgres
    database_url: str

    # Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""

    # S3
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "compliance-docs"
    s3_region: str = "us-east-1"

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://ollama:11434"
    litellm_default_model: str = "gpt-4o-mini"
    litellm_reasoning_model: str = "gpt-4o"
    litellm_local_model: str = "ollama/llama3.1"

    # Embeddings / transcription
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    openai_whisper_model: str = "whisper-1"

    # Ingestion tuning
    chunk_size: int = 1000
    chunk_overlap: int = 150
    qdrant_collection: str = "document_chunks"
    max_upload_mb: int = 50

    # Notifications
    slack_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
