import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Universal Intelligence Engine (UIE)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "uie-super-secret-production-grade-encryption-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./uie.db"
    )

    # Redis / Queue
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    # Search & OSINT
    SEARXNG_URL: str = os.getenv("SEARXNG_URL", "http://localhost:8080")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    USER_AGENT: str = "UIE-Research-Agent/1.0 (+https://github.com/universal-intelligence-engine)"
    
    # LLM Settings
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "heuristic") # "openai", "anthropic", "ollama", "heuristic"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Safety, Privacy & Compliance
    DATA_RETENTION_DAYS: int = 30
    MAX_WORKER_TIMEOUT_SECONDS: int = 60
    MAX_RESULT_SIZE: int = 500

settings = Settings()
