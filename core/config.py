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
    cors_allow_origins: str = "http://localhost:5173,http://localhost:3000"

    database_url: str = (
        "postgresql+psycopg2://kappa:kappa@localhost:5432/kappa_db"
    )
    sqlalchemy_echo: bool = False

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    xp_por_nivel: int = 5000

    # Judge0 — deixe em branco para usar o MockEngineIA (desenvolvimento)
    judge0_base_url: str = ""
    judge0_api_key: str = ""
    judge0_language_id: int = 71  # 71 = Python 3

    @property
    def cors_origins(self) -> list[str]:
        if self.debug:
            return ["*"]
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
