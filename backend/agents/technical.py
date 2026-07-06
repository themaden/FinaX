"""
FinanX — Teknik Analiz Ajanı
Canlı fiyat verileri alıp RSI, MACD ve MA indikatörlerini yorumlar.
"""

import asyncio
from typing import Dict, Any, Optional
from loguru import logger

from backend.llm_factory import get_llm
from backend.tools.live_price import live_price_service, get_historical_async
from backend.tools.indicators import technical_indicators


TECHNICAL_SYSTEM_PROMPT = """Sen FinanX'ın Teknik Analiz Uzmanısın.
Sana verilen teknik göstergeleri yorumlayarak alım/satım/bekleme sinyali üret.

ANALİZ KAPSAMI:
1. RSI (Göreceli Güç Endeksi): 30 altı aşırı satım, 70 üstü aşırı alım
2. MACD: Sinyal çizgisi geçişleri ve histogram yönü
3. Hareketli Ortalamalar: MA20/MA50 kesişme noktaları, altın/ölüm çapraz
4. Bollinger Bantları: Fiyatın bant konumu
5. Destek/Direnç Seviyeleri: Kritik fiyat noktaları

YANIT FORMATI:
📊 TEKNİK TABLO
- RSI: [değer] → [yorum]
- MACD: [yorum]
- MA20/MA50: [yorum]

🎯 SİNYAL VE YORUM
[Detaylı teknik yorum]

⚡ SONUÇ: [GÜÇLÜ ALIM / ALIM / BEKLEME / SATIM / GÜÇLÜ SATIM]

Her zaman Türkçe yanıt ver."""


class TechnicalAnalystAgent:
    """
    Teknik analiz yapan uzman ajan.
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
        period: str = "6mo",
    ) -> Dict[str, Any]:
        """
        Hisse için teknik analiz yap.

        Args:
            ticker: Hisse sembolü
            period: Analiz periyodu (1mo, 3mo, 6mo, 1y)

        Returns:
            Dict: Teknik analiz sonuçları
        """
        ticker = ticker.upper()
        logger.info(f"Teknik analiz başlatıldı: {ticker} ({period})")

        # Tarihsel veri çek
        try:
            df = await get_historical_async(ticker, period=period, interval="1d")
        except Exception as e:
            logger.error(f"Tarihsel veri hatası {ticker}: {e}")
            return {
                "ticker": ticker,
                "agent": "technical_analyst",
                "error": f"Veri çekilemedi: {str(e)}",
                "analysis": "Teknik analiz için veri bulunamadı.",
            }

        if df is None or df.empty:
            return {
                "ticker": ticker,
                "agent": "technical_analyst",
                "error": "Veri yok",
                "analysis": f"{ticker} için tarihsel fiyat verisi bulunamadı.",
            }

        # Teknik indikatörleri hesapla
        try:
            indicators = technical_indicators.analyze(df, ticker=ticker)
        except Exception as e:
            logger.error(f"İndikatör hesaplama hatası: {e}")
            indicators = {"error": str(e)}

        if indicators.get("error"):
            return {
                "ticker": ticker,
                "agent": "technical_analyst",
                "error": indicators["error"],
                "analysis": "Teknik göstergeler hesaplanamadı.",
            }

        # LLM ile yorumla
        indicators_text = self._format_indicators(indicators)

        messages = [
            {"role": "system", "content": TECHNICAL_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{ticker} hissesi için teknik göstergeler:\n\n"
                    f"{indicators_text}"
                ),
            },
        ]

        try:
            llm = self._get_llm()
            response = await llm.ainvoke(messages)
            analysis_text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM teknik analiz hatası: {e}")
            analysis_text = f"Teknik analiz yorumu tamamlanamadı: {str(e)}"

        return {
            "ticker": ticker,
            "agent": "technical_analyst",
            "analysis": analysis_text,
            "indicators": indicators,
            "overall_signal": indicators.get("overall_signal", "YATAY"),
        }

    def _format_indicators(self, ind: Dict[str, Any]) -> str:
        """İndikatörleri LLM'e göndermek için formatla."""
        lines = [
            f"Anlık Fiyat: {ind.get('current_price')} TL",
            f"Günlük Değişim: %{ind.get('price_change_pct', 0):.2f}",
            "",
            "📊 RSI (14):",
            f"  Değer: {ind.get('rsi', {}).get('value')}",
            f"  Sinyal: {ind.get('rsi', {}).get('signal')}",
            "",
            "📊 MACD (12,26,9):",
            f"  MACD: {ind.get('macd', {}).get('macd')}",
            f"  Sinyal: {ind.get('macd', {}).get('signal')}",
            f"  Histogram: {ind.get('macd', {}).get('histogram')}",
            "",
            "📊 Hareketli Ortalamalar:",
            f"  SMA 20: {ind.get('moving_averages', {}).get('sma_20')}",
            f"  SMA 50: {ind.get('moving_averages', {}).get('sma_50')}",
            f"  EMA 20: {ind.get('moving_averages', {}).get('ema_20')}",
            "",
            "📊 Bollinger Bantları:",
            f"  Üst Bant: {ind.get('bollinger', {}).get('upper')}",
            f"  Orta Bant: {ind.get('bollinger', {}).get('middle')}",
            f"  Alt Bant: {ind.get('bollinger', {}).get('lower')}",
            "",
            "📊 Destek/Direnç:",
            f"  Destek: {ind.get('support_resistance', {}).get('support')}",
            f"  Direnç: {ind.get('support_resistance', {}).get('resistance')}",
            "",
            "Mevcut Sinyaller:",
        ]
        for signal in ind.get("signals", []):
            lines.append(f"  • {signal}")

        return "\n".join(lines)


# Singleton
technical_agent = TechnicalAnalystAgent()
