from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Plataforma Kappa API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg2://kappa:kappa@localhost:5432/kappa_db"
    )
    sqlalchemy_echo: bool = False

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    xp_por_nivel: int = 5000


@lru_cache
def get_settings() -> Settings:
    return Settings()
