"""
FinanX — Uygulama Konfigürasyonu
Pydantic Settings v2 ile .env dosyasından ayarları yükler.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # LLM
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-1.5-pro"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Veritabanı
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/finanx.db"

    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = "change_me_in_production"
    DEBUG: bool = True

    # Frontend
    BACKEND_URL: str = "http://localhost:8000"

    # RAG
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    PDF_REPORTS_PATH: str = "./data/reports"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVER_TOP_K: int = 5

    # Zamanlayıcı
    WATCHER_INTERVAL_MINUTES: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
