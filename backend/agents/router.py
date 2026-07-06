"""
FinanX — LLM Router
Kullanıcı sorgusunu analiz edip doğru modüle yönlendirir:
RAG (geçmiş veriler) | LIVE (anlık borsa) | MULTI_AGENT (karmaşık analiz)
"""

from enum import Enum
from typing import Dict, Any, Optional, List
import re
from loguru import logger

from backend.llm_factory import get_fast_llm


class RouteType(str, Enum):
    RAG = "rag"                   # Geçmiş raporlar, finansal tablolar
    LIVE_PRICE = "live_price"     # Anlık fiyat, hacim, değişim
    TECHNICAL = "technical"       # Teknik analiz, indikatörler
    MULTI_AGENT = "multi_agent"   # Kapsamlı şirket analizi
    COMPARE = "compare"           # İki hisseyi karşılaştır
    PORTFOLIO = "portfolio"       # Portföy analizi
    KAP = "kap"                   # KAP bildirimleri


ROUTER_SYSTEM_PROMPT = """Sen bir finansal soru sınıflandırıcısısın.
Kullanıcının sorusunu analiz ederek aşağıdaki kategorilerden birine atfet:

KATEGORILER:
- RAG: Geçmiş raporlar, bilançolar, finansal tablolar, KAP belgeleri, şirket geçmişi
  Örnekler: "2023 net kârı nedir?", "son bilanço", "faaliyet raporu", "vergi ödemeleri"

- LIVE_PRICE: Anlık fiyat, günlük değişim, hacim, piyasa değeri, F/K oranı
  Örnekler: "bugünkü fiyat", "şu an kaç TL", "günlük değişim", "son fiyat"

- TECHNICAL: Teknik analiz, RSI, MACD, hareketli ortalama, trend
  Örnekler: "RSI değeri nedir", "teknik analiz", "trend nerede", "alım satım sinyali"

- MULTI_AGENT: Kapsamlı analiz, yatırım tavsiyesi, şirket değerlendirmesi
  Örnekler: "THYAO hakkında tam analiz yap", "yatırım yapmalı mıyım", "şirket değerlendir"

- COMPARE: İki şirketi karşılaştır
  Örnekler: "THYAO ile PEGYS'ı karşılaştır", "hangi hisse daha iyi"

- PORTFOLIO: Portföy analizi, risk değerlendirmesi
  Örnekler: "portföyümü analiz et", "risk durumu", "portföy çeşitlendirme"

- KAP: KAP bildirimleri, haberler, duyurular
  Örnekler: "son KAP bildirimleri", "yeni duyurular", "temettü haberi"

YANIT FORMATI (yalnızca JSON):
{"route": "KATEGORI", "ticker": "HISSE_SEMBOLÜ_VEYA_NULL", "confidence": 0.0-1.0}"""


class RouterResult:
    def __init__(self, route: RouteType, ticker: Optional[str], confidence: float, raw_query: str):
        self.route = route
        self.ticker = ticker
        self.confidence = confidence
        self.raw_query = raw_query

    def __repr__(self):
        return f"<Route {self.route} ticker={self.ticker} conf={self.confidence:.2f}>"


class LLMRouter:
    """
    LLM tabanlı akıllı soru yönlendiricisi.
    Hızlı sınıflandırma için gemini-flash veya gpt-4o-mini kullanır.
    """

    def __init__(self):
        self._llm = None
        # Kural tabanlı hızlı eşleştirme (LLM çağrısından önce)
        self._quick_patterns = {
            RouteType.LIVE_PRICE: [
                r"bugün[kü]*\s+fiyat", r"şu\s+an[ki]*", r"anlık\s+fiyat",
                r"kaç\s+(?:tl|lira|para)", r"son\s+fiyat", r"güncel\s+fiyat", r"piyasa\s+değer",
                r"fiyatı\s+nedir", r"ne\s+kadar", r"kaç\s+lira",
            ],
            RouteType.TECHNICAL: [
                r"\brsi\b", r"\bmacd\b", r"hareketli\s+ortalama", r"teknik\s+analiz",
                r"bollinger", r"trend", r"destek\s+direnç", r"alım\s+sinyali",
                r"satım\s+sinyali", r"fibonacci",
            ],
            RouteType.KAP: [
                r"\bkap\b", r"bildirim", r"duyur", r"temettü", r"genel\s+kurul",
                r"haberler?", r"açıklama",
            ],
            RouteType.COMPARE: [
                r"karşılaştır", r"ile\s+mi", r"hangisi\s+daha", r"vs\b", r"versus",
                r"mı\s+yoksa",
            ],
            RouteType.PORTFOLIO: [
                r"portföy", r"portfolio", r"risk", r"çeşitlendirme", r"beta",
            ],
            RouteType.MULTI_AGENT: [
                r"tam\s+analiz", r"kapsamlı\s+analiz", r"yatırım\s+yapmalı",
                r"değerlendir", r"rapor\s+yaz", r"incele",
            ],
        }

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_fast_llm()
        return self._llm

    def _extract_ticker_from_query(self, query: str) -> Optional[str]:
        """Sorgudaki BIST sembolünü hızlıca çıkar."""
        # Büyük harf kelimeler (THYAO, EREGL gibi)
        matches = re.findall(r'\b([A-Z]{2,6})\b', query.upper())
        # Yaygın BIST sembolleri
        KNOWN_TICKERS = {
            "THYAO", "EREGL", "AKBNK", "GARAN", "YKBNK", "ISCTR", "HALKB",
            "KCHOL", "SAHOL", "VESTL", "ARCLK", "BIMAS", "MGROS", "TUPRS",
            "TOGG", "ENKAI", "TKFEN", "ULKER", "AEFES", "PETKM", "TAVHL",
            "TCELL", "TTKOM", "ALARK", "LOGO", "PGSUS", "THYAO", "SISE",
            "KOZAL", "CIMSA", "EKGYO",
        }
        for match in matches:
            if match in KNOWN_TICKERS:
                return match
        # İlk 3-6 büyük harf blok
        for match in matches:
            if 3 <= len(match) <= 6:
                return match
        return None

    def _quick_route(self, query: str) -> Optional[RouteType]:
        """Regex tabanlı hızlı yönlendirme (LLM gerektirmez)."""
        query_lower = query.lower()
        for route_type, patterns in self._quick_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return route_type
        return None

    async def route(self, query: str) -> RouterResult:
        """
        Kullanıcı sorgusunu analiz edip yönlendirme kararı ver.

        Args:
            query: Kullanıcının Türkçe sorusu

        Returns:
            RouterResult: Yönlendirme kararı
        """
        ticker = self._extract_ticker_from_query(query)

        # 1. Hızlı regex yönlendirme (LLM masrafı olmadan)
        quick_result = self._quick_route(query)
        if quick_result:
            logger.info(f"Hızlı yönlendirme: '{query[:40]}' → {quick_result} (ticker={ticker})")
            return RouterResult(
                route=quick_result,
                ticker=ticker,
                confidence=0.85,
                raw_query=query,
            )

        # 2. LLM tabanlı yönlendirme
        try:
            import json
            messages = [
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Soru: {query}"},
            ]

            llm = self._get_llm()
            response = await llm.ainvoke(messages)
            text = response.content if hasattr(response, "content") else str(response)

            # JSON'ı temizle ve parse et
            text = text.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            parsed = json.loads(text)
            route_str = parsed.get("route", "RAG").upper()
            llm_ticker = parsed.get("ticker")
            confidence = float(parsed.get("confidence", 0.7))

            # Route enum'a dönüştür
            route_map = {
                "RAG": RouteType.RAG,
                "LIVE_PRICE": RouteType.LIVE_PRICE,
                "TECHNICAL": RouteType.TECHNICAL,
                "MULTI_AGENT": RouteType.MULTI_AGENT,
                "COMPARE": RouteType.COMPARE,
                "PORTFOLIO": RouteType.PORTFOLIO,
                "KAP": RouteType.KAP,
            }
            route = route_map.get(route_str, RouteType.RAG)

            # Ticker'ı birleştir
            final_ticker = ticker or (llm_ticker if llm_ticker != "null" else None)

            logger.info(
                f"LLM yönlendirme: '{query[:40]}' → {route} "
                f"(ticker={final_ticker}, güven={confidence:.2f})"
            )

            return RouterResult(
                route=route,
                ticker=final_ticker,
                confidence=confidence,
                raw_query=query,
            )

        except Exception as e:
            logger.warning(f"Router LLM hatası, RAG'a yönlendiriliyor: {e}")
            # Hata durumunda RAG'a yönlendir
            return RouterResult(
                route=RouteType.RAG,
                ticker=ticker,
                confidence=0.5,
                raw_query=query,
            )


# Singleton
llm_router = LLMRouter()
