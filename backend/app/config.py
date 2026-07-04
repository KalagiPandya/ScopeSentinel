from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # PostgreSQL
    DATABASE_URL: str = "postgresql://scopeuser:scopepass@localhost:5432/scopesentinel"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "scopepass123"

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "scopesentinel_checkpoints"

    # AI Keys — Optional so app starts even without them
    # These are only needed when AI agent routes are called
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Auth
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080

    # GitHub
    GITHUB_WEBHOOK_SECRET: str = ""

    # Notifications (Agent 8) — optional, falls back to console stubs if unset
    SLACK_WEBHOOK_URL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "scopesentinel@example.com"

    # App
    APP_ENV: str = "development"

    # CORS — comma-separated list of allowed frontend origins.
    # Defaults cover local dev. Add your deployed Vercel URL in production,
    # e.g. CORS_ORIGINS=https://scopesentinel.vercel.app,http://localhost:5173
    CORS_ORIGINS_RAW: str = "http://localhost:5173,http://localhost:3000"

    @property
    def CORS_ORIGINS(self) -> list:
        return [o.strip() for o in self.CORS_ORIGINS_RAW.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"  # don't crash on unknown keys in .env


settings = Settings()
