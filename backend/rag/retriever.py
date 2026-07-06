"""
FinanX — RAG Retriever ve LLM Yanıt Üretme
FAISS'ten benzer chunk'ları alıp LLM ile Türkçe yanıt üretir.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from backend.config import settings
from backend.rag.vectorstore import vector_store
from backend.llm_factory import get_llm


RAG_SYSTEM_PROMPT = """Sen FinanX adlı Türkiye borsası (BIST) uzmanı bir finans analistisisin.
Görevin, sana verilen kaynak belgelerden (faaliyet raporları, KAP bildirimleri, finansal tablolar) 
kullanıcının sorularını doğru ve kapsamlı şekilde yanıtlamaktır.

KURALLAR:
1. YALNIZCA verilen kaynak belgelerindeki bilgileri kullan
2. Belgede olmayan bilgiler için "Bu bilgiye sahip değilim" de
3. Finansal rakamlarda daima kaynağı (sayfa/belge adı) belirt
4. Yanıtını Türkçe ver
5. Yanıtı yapılandır: önce özet, sonra detaylar
6. Tablo formatındaki verileri düzgün sun"""


class RAGRetriever:
    """
    RAG (Retrieval-Augmented Generation) motoru.
    Kullanıcı sorgusunu alır → FAISS'ten benzer chunk'ları getirir →
    LLM ile bağlama dayalı yanıt üretir.
    """

    def __init__(self):
        self.llm = None  # Lazy loading

    def _get_llm(self):
        if self.llm is None:
            self.llm = get_llm()
        return self.llm

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        ticker_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sorguya en benzer belge parçalarını getir.

        Returns:
            List[Dict]: Benzer chunk'lar (text, metadata, score)
        """
        return vector_store.search(
            query=query,
            top_k=top_k,
            ticker_filter=ticker_filter,
            score_threshold=0.25,
        )

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Chunk listesinden LLM için bağlam metni oluştur."""
        context_parts = []

        for i, chunk in enumerate(chunks, start=1):
            meta = chunk["metadata"]
            source_info = []

            if meta.get("filename"):
                source_info.append(meta["filename"])
            if meta.get("ticker"):
                source_info.append(f"Hisse: {meta['ticker']}")
            if meta.get("year"):
                source_info.append(f"Yıl: {meta['year']}")
            if meta.get("quarter"):
                source_info.append(f"Çeyrek: Q{meta['quarter']}")

            source_label = " | ".join(source_info) if source_info else f"Kaynak {i}"
            score_pct = int(chunk["score"] * 100)

            context_parts.append(
                f"[{i}. KAYNAK: {source_label} (benzerlik: %{score_pct})]\n"
                f"{chunk['text']}"
            )

        return "\n\n---\n\n".join(context_parts)

    async def query(
        self,
        question: str,
        ticker_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Kullanıcı sorusunu RAG pipeline'ından geçirip yanıt üret.

        Args:
            question: Kullanıcının Türkçe sorusu
            ticker_filter: Belirli bir hisseyle sınırla
            top_k: Kullanılacak chunk sayısı

        Returns:
            Dict: {
                "answer": str,
                "sources": List[Dict],
                "chunk_count": int,
                "has_context": bool
            }
        """
        # 1. Benzer chunk'ları getir
        chunks = self.retrieve(question, top_k=top_k, ticker_filter=ticker_filter)

        if not chunks:
            return {
                "answer": (
                    "⚠️ Bu soruya cevap verebilmek için ilgili belgeler sistemde bulunamadı. "
                    "Lütfen önce şirketin faaliyet raporlarını veya KAP bildirimlerini sisteme yükleyin."
                ),
                "sources": [],
                "chunk_count": 0,
                "has_context": False,
            }

        # 2. Bağlam oluştur
        context = self._build_context(chunks)

        # 3. LLM prompt
        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Aşağıdaki kaynak belgelerini kullanarak soruyu yanıtla:\n\n"
                    f"=== KAYNAK BELGELER ===\n{context}\n\n"
                    f"=== SORU ===\n{question}"
                ),
            },
        ]

        logger.info(f"RAG sorgusu: '{question[:60]}' → {len(chunks)} chunk")

        llm = self._get_llm()
        response = await llm.ainvoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)

        # 4. Kaynak bilgilerini düzenle
        sources = [
            {
                "filename": c["metadata"].get("filename", "bilinmiyor"),
                "ticker": c["metadata"].get("ticker"),
                "year": c["metadata"].get("year"),
                "quarter": c["metadata"].get("quarter"),
                "score": round(c["score"], 3),
                "preview": c["text"][:150] + "...",
            }
            for c in chunks
        ]

        return {
            "answer": answer,
            "sources": sources,
            "chunk_count": len(chunks),
            "has_context": True,
        }


# Singleton instance
rag_retriever = RAGRetriever()
