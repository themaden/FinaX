"""
FinanX — KAP Duygu Analizi Modülü
KAP bildirimlerini LLM ile Pozitif/Negatif/Nötr olarak sınıflandırır.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from backend.llm_factory import get_fast_llm


SENTIMENT_SYSTEM_PROMPT = """Sen Türkiye borsası (BIST) ve KAP bildirimleri konusunda uzman 
bir finans analistisin. Sana verilen KAP bildirimini veya haber metnini analiz et.

GÖREV:
1. Metnin hisse senedi fiyatı üzerindeki etkisini değerlendir
2. Duygu sınıfı belirle: POZİTİF, NEGATİF veya NÖTR
3. Kısa bir özet çıkar (2-3 cümle)

YANIT FORMATI (kesinlikle bu formatı kullan):
DUYGU: [POZİTİF/NEGATİF/NÖTR]
ÖZET: [2-3 cümlelik açıklama]
ETKI: [YÜKSEK/ORTA/DÜŞÜK]

Örnekler:
- Temettü artışı → POZİTİF
- Zarar açıklaması → NEGATİF
- Genel kurul tarih bildirimi → NÖTR
- Büyük sözleşme kazanma → POZİTİF
- Yönetim değişikliği (bağlama göre) → duruma göre"""


class SentimentAnalyzer:
    """
    KAP bildirimleri ve finansal haberleri için duygu analizi.
    """

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_fast_llm()
        return self._llm

    def _parse_sentiment_response(self, response_text: str) -> Dict[str, Any]:
        """LLM yanıtını yapılandırılmış formata dönüştür."""
        lines = response_text.strip().split("\n")
        result = {
            "sentiment": "nötr",
            "summary": response_text[:200],
            "impact": "orta",
        }

        for line in lines:
            line = line.strip()
            # Türkçe karakterleri normalize edip karşılaştır
            normalized_line = line.replace("İ", "I").replace("Ö", "O").replace("Ü", "U").replace("Ş", "S").replace("Ç", "C").replace("Ğ", "G").upper()
            if normalized_line.startswith("DUYGU:"):
                raw = normalized_line.replace("DUYGU:", "").strip()
                if "POZITIF" in raw or "POSITIVE" in raw:
                    result["sentiment"] = "pozitif"
                elif "NEGATIF" in raw or "NEGATIVE" in raw:
                    result["sentiment"] = "negatif"
                else:
                    result["sentiment"] = "nötr"
            elif normalized_line.startswith("OZET:"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    result["summary"] = parts[1].strip()
            elif normalized_line.startswith("ETKI:"):
                raw = normalized_line.replace("ETKI:", "").strip()
                if "YUKSEK" in raw or "HIGH" in raw:
                    result["impact"] = "yüksek"
                elif "DUSUK" in raw or "LOW" in raw:
                    result["impact"] = "düşük"
                else:
                    result["impact"] = "orta"

        return result

    async def analyze(
        self,
        text: str,
        ticker: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tek bir metni analiz et.

        Args:
            text: KAP bildirimi veya haber metni
            ticker: İlgili hisse sembolü (bağlam için)
            title: Bildirim başlığı

        Returns:
            {
                "sentiment": "pozitif"|"negatif"|"nötr",
                "summary": "Kısa özet...",
                "impact": "yüksek"|"orta"|"düşük",
                "ticker": "THYAO",
            }
        """
        if not text or not text.strip():
            return {
                "sentiment": "nötr",
                "summary": "Metin bulunamadı.",
                "impact": "düşük",
                "ticker": ticker,
            }

        # Bağlam zenginleştirme
        context_parts = []
        if ticker:
            context_parts.append(f"Hisse: {ticker}")
        if title:
            context_parts.append(f"Başlık: {title}")
        context = " | ".join(context_parts)

        user_content = f"{context}\n\nBildirim metni:\n{text[:3000]}"

        messages = [
            {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        try:
            llm = self._get_llm()
            response = await llm.ainvoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)

            result = self._parse_sentiment_response(response_text)
            result["ticker"] = ticker

            logger.info(
                f"Duygu analizi: {ticker or 'bilinmiyor'} → "
                f"{result['sentiment']} ({result['impact']})"
            )
            return result

        except Exception as e:
            logger.error(f"Duygu analizi hatası: {e}")
            return {
                "sentiment": "nötr",
                "summary": f"Analiz sırasında hata: {str(e)}",
                "impact": "düşük",
                "ticker": ticker,
            }

    async def analyze_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Birden fazla bildirimi toplu analiz et.

        Args:
            items: [{"text": ..., "ticker": ..., "title": ...}]

        Returns:
            List[Dict]: Her bir bildirimin analiz sonucu
        """
        import asyncio
        tasks = [
            self.analyze(
                text=item.get("text", item.get("summary", "")),
                ticker=item.get("ticker"),
                title=item.get("title"),
            )
            for item in items
        ]
        return await asyncio.gather(*tasks)

    def get_sentiment_emoji(self, sentiment: str) -> str:
        """Duygu için emoji döndür."""
        mapping = {
            "pozitif": "🟢",
            "negatif": "🔴",
            "nötr": "🟡",
        }
        return mapping.get(sentiment.lower(), "⚪")


# Singleton
sentiment_analyzer = SentimentAnalyzer()
