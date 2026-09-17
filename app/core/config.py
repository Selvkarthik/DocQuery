import os
from pathlib import Path
from typing import Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseSettings
    SettingsConfigDict = None

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings if SettingsConfigDict is None else BaseSettings):
    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=str(BASE_DIR / ".env"),
            env_file_encoding="utf-8",
            extra="ignore"
        )
    else:
        class Config:
            env_file = str(BASE_DIR / ".env")
            env_file_encoding = "utf-8"
            extra = "ignore"

    # Project Information
    PROJECT_NAME: str = "DocQuery"
    PROJECT_DESCRIPTION: str = "Production-grade Conversational RAG system with pgvector & Redis Memory"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL & pgvector Database Settings
    DB_USER: str = Field(default="postgres")
    DB_PWD: str = Field(default="postgres")
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB: str = Field(default="rag_db")

    # Redis Memory Settings
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_TTL_SECONDS: int = Field(default=86400 * 7)  # 7 days session retention

    # LLM / OpenRouter Settings
    API_KEY: Optional[str] = Field(default=None)
    OPENROUTER_MODEL: str = Field(default="inclusionai/ling-3.0-flash-fin:free")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    # Embedding Settings
    EMBEDDING_MODEL_NAME: str = Field(default="all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = Field(default=384)

    # RAG Defaults
    DEFAULT_TOP_K: int = Field(default=3)
    DEFAULT_SIMILARITY_THRESHOLD: float = Field(default=0.45)
    MAX_HISTORY_TURNS: int = Field(default=10)

    # Paths
    DOCUMENTS_DIR: Path = BASE_DIR / "documents"

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PWD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB}"


settings = Settings()
