# src/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Code-to-Docs API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Security
    API_KEY_HEADER: str = "X-API-Key"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama3-8b-8192"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.3
    
    # RAG
    VECTOR_DB_PATH: str = "./data/chroma_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_FREE: int = 10
    
    # File limits
    MAX_FILE_SIZE_MB: int = 10
    TEMP_DIR: str = "/tmp/code-to-docs"
    
    # Caching
    CACHE_TTL_SECONDS: int = 86400
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
@lru_cache()
def get_settings() -> Settings:
    return Settings()