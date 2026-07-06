"""
FinanX — Temel Analiz Ajanı
Şirket finansal tablolarını karşılaştırır ve büyüme/borçluluk analizini yapar.
"""

from typing import Dict, Any, Optional
from loguru import logger

from backend.llm_factory import get_llm
from backend.tools.live_price import live_price_service
from backend.rag.retriever import rag_retriever


FUNDAMENTAL_SYSTEM_PROMPT = """Sen FinanX'ın Temel Analiz Uzmanısın.
Görevin BIST şirketlerinin finansal tablolarını analiz etmek ve yorumlamaktır.

ANALİZ KAPSAMI:
1. Gelir Tablosu: Net satışlar, EBITDA, net kâr/zarar trendi
2. Bilanço Analizi: Öz sermaye, toplam borç, net borç/EBITDA
3. Büyüme Rasyoları: Yıllık gelir büyümesi, kâr büyümesi
4. Karlılık: Net kâr marjı, öz sermaye getirisi (ROE), aktif getirisi (ROA)
5. Değerleme: F/K, PD/DD, FD/EBITDA karşılaştırması

YANIT FORMATI:
- Rakamları Türk Lirası ve büyük sayı formatında sun (milyar TL)
- Her bulguyu ❗ (olumsuz) veya ✅ (olumlu) ile işaretle
- Sonunda kısa bir "Temel Analiz Özeti" yaz

Her zaman Türkçe yanıt ver."""


class FundamentalAnalystAgent:
    """
    Şirket finansal tablolarını analiz eden temel analiz ajanı.
    Hem canlı veriden hem RAG'dan bilgi kullanır.
    """

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    async def analyze(
        self,
        ticker: str,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bir şirket için temel analiz yap.

        Args:
            ticker: Hisse sembolü (örn: THYAO)
            query: Opsiyonel özel soru

        Returns:
            Dict: {
                "ticker": ...,
                "analysis": "Türkçe analiz metni",
                "financials": {...},
                "ratios": {...}
            }
        """
        ticker = ticker.upper()
        logger.info(f"Temel analiz başlatıldı: {ticker}")

        # 1. Canlı finansal tablolar
        financials = {}
        quote = {}
        try:
            financials = live_price_service.get_financials(ticker)
            quote = live_price_service.get_quote(ticker)
        except Exception as e:
            logger.warning(f"Finansal veri çekme hatası {ticker}: {e}")

        # 2. RAG'dan geçmiş rapor bilgileri
        rag_context = ""
        try:
            rag_question = query or f"{ticker} şirketinin finansal performansı, kârlılık durumu ve borçluluk analizi"
            rag_result = await rag_retriever.query(
                question=rag_question,
                ticker_filter=ticker,
                top_k=5,
            )
            if rag_result.get("has_context"):
                rag_context = f"\n\nFAALİYET RAPORLARINDAN BİLGİLER:\n{rag_result['answer']}"
        except Exception as e:
            logger.warning(f"RAG sorgusu hatası: {e}")

        # 3. LLM analizi
        context_parts = [f"Hisse Sembolü: {ticker}"]

        if quote and not quote.get("error"):
            context_parts.append(
                f"Anlık Fiyat: {quote.get('price', 'N/A')} TL\n"
                f"Piyasa Değeri: {self._format_market_cap(quote.get('market_cap'))}\n"
                f"F/K Oranı: {quote.get('pe_ratio', 'N/A')}\n"
                f"PD/DD: {quote.get('pb_ratio', 'N/A')}\n"
                f"Temettü Verimi: {quote.get('dividend_yield', 'N/A')}"
            )

        if financials and not financials.get("error"):
            # Gelir tablosundan net kâr al
            income = financials.get("income_statement", {})
            if income:
                latest_year = list(income.keys())[0] if income else None
                if latest_year:
                    year_data = income[latest_year]
                    net_income = year_data.get("Net Income", year_data.get("Net Income Common Stockholders"))
                    total_revenue = year_data.get("Total Revenue")
                    ebitda = year_data.get("EBITDA")

                    context_parts.append(
                        f"\nSON DÖNEM FİNANSAL TABLOLAR ({latest_year}):\n"
                        f"Net Kâr: {self._format_number(net_income)}\n"
                        f"Toplam Ciro: {self._format_number(total_revenue)}\n"
                        f"EBITDA: {self._format_number(ebitda)}"
                    )

        context_parts.append(rag_context)
        full_context = "\n".join(context_parts)

        messages = [
            {"role": "system", "content": FUNDAMENTAL_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Aşağıdaki verileri kullanarak {ticker} için kapsamlı temel analiz yap:\n\n"
                    f"{full_context}\n\n"
                    f"{'Özel soru: ' + query if query else ''}"
                ),
            },
        ]

        try:
            llm = self._get_llm()
            response = await llm.ainvoke(messages)
            analysis_text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM analiz hatası: {e}")
            analysis_text = f"Temel analiz tamamlanamadı: {str(e)}"

        return {
            "ticker": ticker,
            "agent": "fundamental_analyst",
            "analysis": analysis_text,
            "quote_data": quote,
            "financial_data": financials,
        }

    def _format_market_cap(self, value) -> str:
        if value is None:
            return "N/A"
        value = float(value)
        if value >= 1e12:
            return f"{value/1e12:.2f} Trilyon TL"
        elif value >= 1e9:
            return f"{value/1e9:.2f} Milyar TL"
        elif value >= 1e6:
            return f"{value/1e6:.2f} Milyon TL"
        return f"{value:,.2f} TL"

    def _format_number(self, value) -> str:
        if value is None:
            return "N/A"
        try:
            value = float(value)
            if abs(value) >= 1e12:
                return f"{value/1e12:.2f} Trilyon TL"
            elif abs(value) >= 1e9:
                return f"{value/1e9:.2f} Milyar TL"
            elif abs(value) >= 1e6:
                return f"{value/1e6:.2f} Milyon TL"
            return f"{value:,.2f} TL"
        except Exception:
            return "N/A"


# Singleton
fundamental_agent = FundamentalAnalystAgent()
