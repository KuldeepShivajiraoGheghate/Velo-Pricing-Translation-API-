"""
Application settings — loaded from environment variables via pydantic-settings.
All secrets come from environment; never hardcoded.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "local"
    secret_key: str = "change-me-insecure-default"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Database
    database_url: str = "postgresql+psycopg://velo:velo_dev_password@localhost:5432/velo_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # FX Rate Provider
    fx_provider_base_url: str = "https://api.frankfurter.app"
    fx_refresh_interval_minutes: int = 60

    # Stripe (loaded from env — never committed)
    stripe_secret_key: str = ""

    # Chargebee (stub)
    chargebee_site: str = ""
    chargebee_api_key: str = ""

    # Recurly (stub)
    recurly_api_key: str = ""

    # Rate limiting
    rate_limit_per_minute: int = 60

    # CORS
    frontend_origin: str = "http://localhost:5173"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once per process."""
    return Settings()
