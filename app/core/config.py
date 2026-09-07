from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "hiring-assistant"
    ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # PostgreSQL — accepts a full connection URL (e.g. from Neon)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/app"

    # Redis — accepts a full connection URL (e.g. from Upstash, use rediss:// for TLS)
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_PRIVATE_KEY_PATH: str = "keys/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "keys/public.pem"
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "events"

    HUNAR_API_KEY: str = ""
    HUNAR_TIMEOUT_SECONDS: float = 30.0
    HUNAR_WEBHOOK_SECRET: str = ""
    PDL_API_KEY: str = ""
    APOLLO_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url_async(self) -> str:
        """Return the DATABASE_URL adapted for SQLAlchemy asyncpg driver."""
        url = self.DATABASE_URL
        # Replace postgresql:// or postgres:// with the asyncpg dialect
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # asyncpg uses ssl=require instead of sslmode=require
        url = url.replace("sslmode=require", "ssl=require")
        # channel_binding is not supported by asyncpg — strip it
        url = url.replace("&channel_binding=require", "")
        url = url.replace("?channel_binding=require", "")
        return url

    @property
    def service_prefix(self) -> str:
        return "/" + self.APP_NAME.lower().replace(" ", "-")

@lru_cache
def get_settings() -> Settings:
    return Settings()
