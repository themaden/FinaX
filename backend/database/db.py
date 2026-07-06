"""
FinanX — Veritabanı Bağlantı Yönetimi
SQLAlchemy async engine ile SQLite bağlantısı.
"""

import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings


def _ensure_db_dir():
    """SQLite veritabanı dizinini oluştur."""
    db_url = settings.DATABASE_URL
    # sqlite+aiosqlite:///./data/finanx.db → ./data/finanx.db
    if "sqlite" in db_url:
        path_part = db_url.split("///")[-1]
        db_path = Path(path_part)
        db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_db_dir()

# Async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Tüm SQLAlchemy modellerinin temel sınıfı."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency injection için DB session sağlayıcısı."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Tüm tabloları oluştur (uygulama başlangıcında çalışır)."""
    from backend.database import models  # noqa: F401 — modelleri kaydet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
