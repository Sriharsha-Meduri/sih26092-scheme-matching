from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Every value can be overridden by an environment
    variable of the same name (case insensitive), or by a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SIH26092 Scheme Matching Backend"
    app_version: str = "0.1.0"
    env: str = "development"

    database_url: str = "postgresql+psycopg://sih:sih_dev@localhost:5433/sih26092"

    # Comma separated list of allowed origins for the frontend.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Optional regex for additional origins, e.g. Vercel preview deployments of the frontend.
    cors_origin_regex: str | None = r"https://.*\.vercel\.app"

    # Recommendation engine boundary: mock | module | http
    recommendation_engine: str = "mock"
    recommendation_engine_url: str | None = None
    recommendation_engine_module: str | None = None
    recommendation_engine_timeout_seconds: float = 10.0

    default_partner_radius_km: float = 50.0
    max_partner_radius_km: float = 500.0

    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def _normalise_database_url(cls, v: str) -> str:
        """Hosted Postgres (Render, Supabase, Neon, Railway) hands out postgres:// or
        postgresql:// URLs. SQLAlchemy 2 needs the driver spelled out."""
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
