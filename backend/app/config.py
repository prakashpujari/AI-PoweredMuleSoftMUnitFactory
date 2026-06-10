"""Central configuration via Pydantic Settings — all values from env / .env file."""
from functools import lru_cache
from typing import List, Optional

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI-MUnit-Factory"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-256-bit-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://munit:munit_pass@localhost:5432/munit_factory"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    # ── AI Providers ──────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 8192
    GROQ_TEMPERATURE: float = 0.1

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    DEFAULT_AI_PROVIDER: str = "groq"  # groq | anthropic | openai

    # ── Pinecone ──────────────────────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "munit-factory"
    PINECONE_DIMENSION: int = 1536

    # ── MuleSoft / Anypoint ───────────────────────────────────────────────────
    ANYPOINT_CLIENT_ID: str = ""
    ANYPOINT_CLIENT_SECRET: str = ""
    ANYPOINT_ORG_ID: str = ""
    ANYPOINT_ENV_ID: str = ""
    ANYPOINT_BASE_URL: str = "https://anypoint.mulesoft.com"

    # ── GitHub ────────────────────────────────────────────────────────────────
    GITHUB_TOKEN: str = ""
    GITHUB_ORG: str = ""
    REPO_SCAN_PATH: str = "/repos"

    # ── Maven ─────────────────────────────────────────────────────────────────
    MVN_HOME: str = "/usr/local/maven"
    MVN_OPTS: str = "-Xmx2g"

    # ── Observability ─────────────────────────────────────────────────────────
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
    PROMETHEUS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ── Coverage ──────────────────────────────────────────────────────────────
    COVERAGE_TARGET_PERCENT: float = 95.0
    MIN_ACCEPTABLE_COVERAGE: float = 80.0

    @field_validator("APP_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
