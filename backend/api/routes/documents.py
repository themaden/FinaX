"""
FinanX — /documents Endpoint
PDF faaliyet raporu yükleme ve RAG indeksleme işlemleri.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from loguru import logger
from sqlalchemy import select

from backend.config import settings
from backend.rag.ingestion import ingestion_pipeline
from backend.rag.vectorstore import vector_store
from backend.database.db import AsyncSessionLocal
from backend.database.models import DocumentIndex

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE_MB = 50


@router.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ticker: Optional[str] = Form(None),
    doc_type: str = Form(default="faaliyet_raporu"),
    year: Optional[int] = Form(None),
    quarter: Optional[int] = Form(None),
):
    """
    PDF faaliyet raporu veya KAP belgesi yükle ve RAG sistemine ekle.

    - Dosya türü: PDF, TXT veya DOCX
    - Maksimum boyut: 50 MB
    - Yükleme sonrası otomatik indeksleme başlar
    """
    # Dosya türü kontrolü
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya türü: {ext}. Desteklenenler: {ALLOWED_EXTENSIONS}"
        )

    # Boyut kontrolü
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya çok büyük: {size_mb:.1f} MB (maksimum {MAX_FILE_SIZE_MB} MB)"
        )

    # Dosyayı kaydet
    reports_dir = Path(settings.PDF_REPORTS_PATH)
    reports_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{ticker or 'unknown'}_{file.filename}" if ticker else (file.filename or "upload")
    save_path = reports_dir / safe_filename

    with open(save_path, "wb") as fp:
        fp.write(content)

    logger.info(f"Dosya kaydedildi: {save_path} ({size_mb:.1f} MB)")

    # Arka planda indeksle
    background_tasks.add_task(
        _index_document,
        filepath=str(save_path),
        ticker=ticker,
        doc_type=doc_type,
        year=year,
        quarter=quarter,
    )

    return {
        "message": "Dosya yüklendi, RAG indeksleme başlatıldı",
        "filename": safe_filename,
        "size_mb": round(size_mb, 2),
        "ticker": ticker,
        "status": "indexing",
    }


@router.get("/documents")
async def list_documents():
    """Yüklenmiş belgeleri listele."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentIndex).order_by(DocumentIndex.created_at.desc())
        )
        docs = result.scalars().all()

    return {
        "total": len(docs),
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "ticker": d.ticker,
                "doc_type": d.doc_type,
                "year": d.year,
                "quarter": d.quarter,
                "chunk_count": d.chunk_count,
                "is_indexed": d.is_indexed,
                "indexed_at": d.indexed_at.isoformat() if d.indexed_at else None,
            }
            for d in docs
        ],
    }


@router.get("/documents/stats")
async def get_index_stats():
    """FAISS vektör indeks istatistiklerini döndür."""
    return vector_store.get_stats()


@router.delete("/documents/{ticker}")
async def delete_ticker_documents(ticker: str):
    """Belirli bir hisseye ait tüm belgeleri, veritabanı kayıtlarını ve fiziksel dosyaları sil."""
    ticker_upper = ticker.upper()
    deleted_chunks = vector_store.delete_by_ticker(ticker_upper)

    deleted_files = 0
    # 1. Veritabanı kayıtlarını sil ve dosya yollarını al
    from sqlalchemy import delete
    async with AsyncSessionLocal() as session:
        # Önce silinecek belgeleri sorgula
        q = select(DocumentIndex).where(DocumentIndex.ticker == ticker_upper)
        result = await session.execute(q)
        docs = result.scalars().all()

        for doc in docs:
            # Fiziksel dosyayı sil
            filepath = Path(settings.PDF_REPORTS_PATH) / doc.filename
            try:
                if filepath.exists():
                    os.remove(filepath)
                    deleted_files += 1
            except Exception as e:
                logger.error(f"Fiziksel dosya silme hatası ({filepath}): {e}")

        # DB kayıtlarını temizle
        await session.execute(
            delete(DocumentIndex).where(DocumentIndex.ticker == ticker_upper)
        )
        await session.commit()

    return {
        "message": f"{ticker_upper} belgeleri, veritabanı kayıtları ve fiziksel dosyaları silindi",
        "deleted_chunks": deleted_chunks,
        "deleted_files": deleted_files,
    }


async def _index_document(
    filepath: str,
    ticker: Optional[str],
    doc_type: str,
    year: Optional[int],
    quarter: Optional[int],
):
    """Arka planda belgeyi indeksle."""
    logger.info(f"İndeksleme başlatıldı: {filepath}")

    try:
        chunks = ingestion_pipeline.ingest_pdf(
            filepath=filepath,
            ticker=ticker,
            doc_type=doc_type,
            year=year,
            quarter=quarter,
        )

        if chunks:
            added = vector_store.add_chunks(chunks)

            # Veritabanına kaydet
            file_hash = ingestion_pipeline.compute_file_hash(filepath)
            async with AsyncSessionLocal() as db_session:
                doc = DocumentIndex(
                    filename=os.path.basename(filepath),
                    ticker=ticker,
                    doc_type=doc_type,
                    year=year,
                    quarter=quarter,
                    chunk_count=added,
                    is_indexed=True,
                    file_hash=file_hash,
                    indexed_at=datetime.utcnow(),
                )
                db_session.add(doc)
                await db_session.commit()

            logger.success(f"✅ İndeksleme tamamlandı: {added} chunk ({filepath})")
        else:
            logger.warning(f"İndeksleme: chunk oluşturulamadı ({filepath})")

    except Exception as e:
        logger.error(f"İndeksleme hatası {filepath}: {e}", exc_info=True)
