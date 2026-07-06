"""
FinanX — Embedding Modülü
sentence-transformers ile Türkçe destekli çok dilli embedding üretimi.
"""

import os
from typing import List, Optional
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from backend.config import settings


class EmbeddingService:
    """
    Türkçe finansal metinleri vektöre dönüştüren embedding servisi.
    paraphrase-multilingual-mpnet-base-v2 modeli kullanır.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model: Optional[SentenceTransformer] = None
        self.embedding_dim: int = 768  # mpnet-base-v2 için

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading — ilk kullanımda modeli yükle."""
        if self._model is None:
            logger.info(f"Embedding modeli yükleniyor: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self.embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.success(f"✅ Embedding modeli yüklendi (dim={self.embedding_dim})")
        return self._model

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Metin listesini vektör matrisine dönüştür.

        Args:
            texts: Embedding'i alınacak metin listesi
            batch_size: Batch boyutu (bellek optimizasyonu)
            show_progress: İlerleme çubuğu göster

        Returns:
            np.ndarray: shape (n_texts, embedding_dim), dtype=float32
        """
        if not texts:
            return np.array([], dtype=np.float32)

        logger.info(f"{len(texts)} metin embed ediliyor (batch_size={batch_size})...")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2 normalizasyon (cosine similarity için)
        )

        logger.success(f"✅ {len(texts)} metin embed edildi → shape={embeddings.shape}")
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Tek bir kullanıcı sorgusunu embed et.
        Arama sırasında kullanılır.

        Returns:
            np.ndarray: shape (1, embedding_dim), dtype=float32
        """
        embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding.astype(np.float32)

    def get_embedding_dim(self) -> int:
        """Embedding boyutunu döndür."""
        _ = self.model  # modeli yükle
        return self.embedding_dim


# Singleton instance
embedding_service = EmbeddingService()
