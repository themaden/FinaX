"""
FinanX — FastAPI Uygulama Giriş Noktası
Tüm route'ları, middleware'leri ve yaşam döngüsü yönetimini içerir.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from backend.config import settings
from backend.database.db import init_db
from backend.alarms.scheduler import alarm_scheduler

# Route'ları import et
from backend.api.routes import query, compare, alarms, portfolio, documents


# ─── Logging Konfigürasyonu ─────────────────────────────────────────────────
# Windows terminallerinde Türkçe karakter kodlamasından (cp1254) kaynaklı 
# emoji (🚀, ✅ vb.) yazdırma hatalarını önlemek için stdout'u UTF-8'e zorla.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger.remove()
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="DEBUG" if settings.DEBUG else "INFO",
)
logger.add("logs/finanx_{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days")


# ─── Yaşam Döngüsü ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıç ve kapanış işlemleri."""
    logger.info("🚀 FinanX API başlatılıyor...")

    # Veritabanı tablolarını oluştur
    await init_db()
    logger.success("✅ Veritabanı hazır")

    # Alarm zamanlayıcısını başlat
    alarm_scheduler.start()
    logger.success("✅ Alarm zamanlayıcısı aktif")

    logger.success(
        f"✅ FinanX API hazır → "
        f"http://{settings.API_HOST}:{settings.API_PORT}/docs"
    )

    yield  # Uygulama çalışıyor

    # Kapanış
    alarm_scheduler.stop()
    logger.info("FinanX API kapatıldı")


# ─── FastAPI Uygulaması ──────────────────────────────────────────────────────
app = FastAPI(
    title="FinanX API",
    description=(
        "BIST Yapay Zeka Finansal Analiz Platformu. "
        "RAG tabanlı geçmiş analiz, çoklu ajan mimarisi, "
        "canlı borsa verisi ve Telegram alarm sistemi."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─── CORS Middleware ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da kısıtla
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Hata Yakalama ────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Beklenmeyen hata: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Sunucu hatası",
            "detail": str(exc) if settings.DEBUG else "Lütfen daha sonra tekrar deneyin",
        },
    )


# ─── Route'lar ──────────────────────────────────────────────────────────────
app.include_router(query.router, prefix="/api/v1", tags=["Sorgular"])
app.include_router(compare.router, prefix="/api/v1", tags=["Karşılaştırma"])
app.include_router(alarms.router, prefix="/api/v1", tags=["Alarmlar"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["Portföy"])
app.include_router(documents.router, prefix="/api/v1", tags=["Belgeler"])


# ─── Sağlık Kontrol Endpoint'i ───────────────────────────────────────────────
@app.get("/health", tags=["Sistem"])
async def health_check():
    """API sağlık durumunu kontrol et."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
        "alarm_scheduler": alarm_scheduler.is_running,
        "scheduler_jobs": alarm_scheduler.get_jobs_info(),
    }


@app.get("/", tags=["Sistem"])
async def root():
    """API ana sayfası."""
    return {
        "app": "FinanX API",
        "description": "BIST AI Finansal Analiz Platformu",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
