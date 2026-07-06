"""
FinanX — RAG Sistemi Testleri
FAISS arama kalitesi ve hallucination kontrolü.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import os


@pytest.fixture(scope="module")
def sample_text():
    return """
    THYAO 2023 Yılı Faaliyet Raporu
    
    Net Kâr: 42.7 Milyar TL (2022: 18.3 Milyar TL, %133 artış)
    Toplam Ciro: 185.4 Milyar TL
    EBITDA: 67.2 Milyar TL
    Yolcu Sayısı: 83.4 Milyon (Rekor)
    Temettü: Hisse başına 8.50 TL
    
    Önemli Gelişmeler:
    - 21 yeni uçak filosuna katıldı
    - Yeni 15 destinasyon eklendi
    - Star Alliance üyeliği devam ediyor
    """


@pytest.mark.asyncio
async def test_ingestion_pipeline(sample_text):
    """Metin chunking'in doğru çalışıp çalışmadığını test et."""
    from backend.rag.ingestion import PDFIngestionPipeline

    pipeline = PDFIngestionPipeline()
    chunks = pipeline.ingest_text(
        text=sample_text,
        metadata={"ticker": "THYAO", "source": "test"},
    )

    assert len(chunks) > 0, "En az 1 chunk oluşturulmalı"
    assert all(len(c.text) > 0 for c in chunks), "Chunk'lar boş olmamalı"
    assert all(c.metadata.get("ticker") == "THYAO" for c in chunks), "Metadata korunmalı"

    print(f"✅ Chunking: {len(chunks)} chunk oluşturuldu")


@pytest.mark.asyncio
async def test_embedding_generation():
    """Embedding boyutunun doğru olduğunu test et."""
    from backend.rag.embedder import EmbeddingService

    service = EmbeddingService()
    texts = ["THYAO hissesi güçlü finansal göstergeler açıkladı", "Net kâr artışı bekleniyor"]
    embeddings = service.embed_texts(texts)

    assert embeddings.shape[0] == 2, "2 metin için 2 embedding olmalı"
    assert embeddings.shape[1] > 0, "Embedding boyutu pozitif olmalı"

    print(f"✅ Embedding: shape={embeddings.shape}")


@pytest.mark.asyncio
async def test_vectorstore_add_and_search(sample_text):
    """FAISS'e ekleme ve arama testi."""
    import tempfile
    from backend.rag.ingestion import PDFIngestionPipeline
    from backend.rag.vectorstore import FAISSVectorStore

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = PDFIngestionPipeline()
        store = FAISSVectorStore(index_path=tmpdir)

        chunks = pipeline.ingest_text(
            sample_text,
            metadata={"ticker": "THYAO", "source": "test"},
        )
        added = store.add_chunks(chunks)
        assert added > 0, "Chunk'lar eklenmeli"

        results = store.search("THYAO net kârı ne kadar?", top_k=3)
        assert len(results) > 0, "Arama sonuç döndürmeli"
        assert results[0]["score"] > 0, "Benzerlik skoru pozitif olmalı"

        print(f"✅ FAISS: {added} chunk eklendi, arama {len(results)} sonuç döndürdü")


@pytest.mark.asyncio
async def test_hallucination_prevention(sample_text):
    """RAG'ın belgede olmayan bilgi üretmediğini test et."""
    from backend.rag.ingestion import PDFIngestionPipeline
    from backend.rag.vectorstore import FAISSVectorStore

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = PDFIngestionPipeline()
        store = FAISSVectorStore(index_path=tmpdir)

        chunks = pipeline.ingest_text(
            sample_text,
            metadata={"ticker": "THYAO", "source": "test"},
        )
        store.add_chunks(chunks)

        # Belgede olmayan konuda arama
        results = store.search(
            "PETKM hissesinin 2023 üretim kapasitesi",
            top_k=3,
            ticker_filter="PETKM",
        )
        assert len(results) == 0, "PETKM belgesi yoksa sonuç olmamalı (hallucination engeli)"
        print("✅ Hallucination testi: Yanlış ticker için sonuç dönmedi")


def test_ticker_extraction():
    """Router'ın ticker çıkarma fonksiyonunu test et."""
    from backend.agents.router import LLMRouter

    router = LLMRouter()
    assert router._extract_ticker_from_query("THYAO bugün ne kadar?") == "THYAO"
    assert router._extract_ticker_from_query("Garanti bankası analizi") is None

    print("✅ Ticker çıkarma testi başarılı")


def test_quick_routing():
    """Regex tabanlı hızlı yönlendirmeyi test et."""
    from backend.agents.router import LLMRouter, RouteType

    router = LLMRouter()
    assert router._quick_route("THYAO bugünkü fiyatı nedir") == RouteType.LIVE_PRICE
    assert router._quick_route("RSI değeri ne durumda") == RouteType.TECHNICAL
    assert router._quick_route("son KAP bildirimleri") == RouteType.KAP
    assert router._quick_route("portföy riski") == RouteType.PORTFOLIO

    print("✅ Hızlı yönlendirme testleri başarılı")
