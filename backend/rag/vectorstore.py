"""
FinanX — FAISS Vektör Veri Tabanı
Belge chunk'larını FAISS IndexFlatIP (iç çarpım) ile saklar ve sorgular.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import faiss
import numpy as np
from loguru import logger

from backend.config import settings
from backend.rag.embedder import embedding_service
from backend.rag.ingestion import DocumentChunk


class FAISSVectorStore:
    """
    FAISS tabanlı vektör veri tabanı.
    Normalize edilmiş vektörler için IndexFlatIP kullanır
    (normalize + iç çarpım = cosine similarity).
    """

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH)
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.faiss_file = self.index_path / "index.faiss"
        self.metadata_file = self.index_path / "metadata.pkl"

        self._index: Optional[faiss.IndexFlatIP] = None
        self._metadata: List[Dict[str, Any]] = []  # chunk metadata listesi
        self._texts: List[str] = []                 # orijinal chunk metinleri

        # Mevcut index'i yükle
        self._load_if_exists()

    def _load_if_exists(self):
        """Diskten mevcut FAISS index'ini yükle."""
        if self.faiss_file.exists() and self.metadata_file.exists():
            try:
                self._index = faiss.read_index(str(self.faiss_file))
                with open(self.metadata_file, "rb") as f:
                    data = pickle.load(f)
                    self._metadata = data.get("metadata", [])
                    self._texts = data.get("texts", [])
                logger.info(
                    f"FAISS index yüklendi: {self._index.ntotal} vektör, "
                    f"{len(self._metadata)} chunk"
                )
            except Exception as e:
                logger.warning(f"Index yüklenemedi, sıfırdan başlanıyor: {e}")
                self._index = None
                self._metadata = []
                self._texts = []

    def _save(self):
        """Index'i diske kaydet."""
        if self._index is not None:
            faiss.write_index(self._index, str(self.faiss_file))
            with open(self.metadata_file, "wb") as f:
                pickle.dump(
                    {"metadata": self._metadata, "texts": self._texts},
                    f,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            logger.info(f"FAISS index kaydedildi: {self._index.ntotal} vektör")

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Chunk listesini embed edip FAISS'e ekle.

        Args:
            chunks: DocumentChunk listesi

        Returns:
            int: Eklenen chunk sayısı
        """
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        embeddings = embedding_service.embed_texts(texts, show_progress=True)

        # Index'i ilk kez oluştur
        if self._index is None:
            dim = embedding_service.get_embedding_dim()
            self._index = faiss.IndexFlatIP(dim)
            logger.info(f"Yeni FAISS IndexFlatIP oluşturuldu (dim={dim})")

        # Vektörleri ekle
        self._index.add(embeddings)
        self._metadata.extend([c.metadata for c in chunks])
        self._texts.extend(texts)

        # Kaydet
        self._save()

        logger.success(f"✅ {len(chunks)} chunk FAISS'e eklendi (toplam: {self._index.ntotal})")
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        ticker_filter: Optional[str] = None,
        score_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Kullanıcı sorgusuna en benzer chunk'ları döndür.

        Args:
            query: Kullanıcının sorusu (Türkçe/İngilizce)
            top_k: Döndürülecek maksimum sonuç sayısı
            ticker_filter: Sadece belirli bir hisse sembolüne filtrele
            score_threshold: Minimum benzerlik skoru (0-1)

        Returns:
            List[Dict]: [{"text": ..., "metadata": ..., "score": ...}]
        """
        if self._index is None or self._index.ntotal == 0:
            logger.warning("FAISS index boş — önce belge yükleyin")
            return []

        k = top_k or settings.RETRIEVER_TOP_K
        # Ticker filtresi varsa daha fazla sonuç al, sonra filtrele
        search_k = k * 5 if ticker_filter else k

        query_vector = embedding_service.embed_query(query)
        scores, indices = self._index.search(query_vector, min(search_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if float(score) < score_threshold:
                continue

            metadata = self._metadata[idx]

            # Ticker filtresi uygula
            if ticker_filter:
                chunk_ticker = metadata.get("ticker", "").upper()
                if chunk_ticker and chunk_ticker != ticker_filter.upper():
                    continue

            results.append({
                "text": self._texts[idx],
                "metadata": metadata,
                "score": float(score),
            })

            if len(results) >= k:
                break

        logger.info(f"Arama: '{query[:50]}' → {len(results)} sonuç (filter={ticker_filter})")
        return results

    def delete_by_ticker(self, ticker: str) -> int:
        """Belirli bir hisseye ait tüm chunk'ları sil."""
        ticker_upper = ticker.upper()
        indices_to_keep = [
            i for i, meta in enumerate(self._metadata)
            if meta.get("ticker", "").upper() != ticker_upper
        ]

        if len(indices_to_keep) == len(self._metadata):
            logger.info(f"Silinecek chunk bulunamadı: {ticker}")
            return 0

        deleted = len(self._metadata) - len(indices_to_keep)

        # Yeni index oluştur
        kept_texts = [self._texts[i] for i in indices_to_keep]
        kept_metadata = [self._metadata[i] for i in indices_to_keep]

        if kept_texts:
            embeddings = embedding_service.embed_texts(kept_texts, show_progress=False)
            dim = embedding_service.get_embedding_dim()
            self._index = faiss.IndexFlatIP(dim)
            self._index.add(embeddings)
        else:
            self._index = None

        self._texts = kept_texts
        self._metadata = kept_metadata
        self._save()

        logger.success(f"✅ {deleted} chunk silindi ({ticker})")
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        """Index istatistiklerini döndür."""
        ticker_counts: Dict[str, int] = {}
        for meta in self._metadata:
            ticker = meta.get("ticker", "bilinmiyor")
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

        return {
            "total_vectors": self._index.ntotal if self._index else 0,
            "total_chunks": len(self._metadata),
            "tickers": ticker_counts,
            "index_path": str(self.index_path),
        }

    @property
    def is_empty(self) -> bool:
        return self._index is None or self._index.ntotal == 0


# Singleton instance
vector_store = FAISSVectorStore()
