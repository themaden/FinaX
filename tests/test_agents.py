"""
FinanX — Ajan Sistemi Testleri
"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_router_rag_detection():
    """RAG yönlendirme testi."""
    from backend.agents.router import LLMRouter, RouteType
    router = LLMRouter()
    result = await router.route("THYAO 2023 faaliyet raporunda ne yazıyor")
    print(f"Route: {result.route} (güven: {result.confidence})")


@pytest.mark.asyncio
async def test_router_live_price_detection():
    """Canlı fiyat yönlendirme testi."""
    from backend.agents.router import LLMRouter, RouteType
    router = LLMRouter()
    result = await router.route("THYAO bugün kaç lira")
    assert result.route == RouteType.LIVE_PRICE
    assert result.ticker == "THYAO"
    print(f"✅ Live price yönlendirme: {result}")


def test_sentiment_parsing():
    """Duygu analizi yanıt ayrıştırma testi."""
    from backend.tools.sentiment import SentimentAnalyzer
    analyzer = SentimentAnalyzer()

    response = "DUYGU: POZİTİF\nÖZET: Şirket güçlü kâr açıkladı.\nETKİ: YÜKSEK"
    result = analyzer._parse_sentiment_response(response)

    assert result["sentiment"] == "pozitif"
    assert result["impact"] == "yüksek"
    assert "güçlü" in result["summary"]
    print(f"✅ Duygu ayrıştırma: {result}")


def test_technical_indicator_rsi():
    """RSI hesaplama doğruluğu testi."""
    import pandas as pd
    import numpy as np
    from backend.tools.indicators import TechnicalIndicators

    ti = TechnicalIndicators()
    # Düzenli artış serisi
    prices = pd.Series([100 + i for i in range(50)])
    rsi = ti.calculate_rsi(prices)

    # Sürekli artışta RSI yüksek olmalı (>70)
    last_rsi = rsi.dropna().iloc[-1]
    assert last_rsi > 70, f"Sürekli artışta RSI > 70 olmalı, şu an: {last_rsi}"
    print(f"✅ RSI testi: {last_rsi:.2f} (yükselişte > 70 ✓)")


def test_market_cap_formatting():
    """Piyasa değeri formatlama testi."""
    from backend.agents.fundamental import FundamentalAnalystAgent
    agent = FundamentalAnalystAgent()

    assert "Trilyon" in agent._format_market_cap(1.5e12)
    assert "Milyar" in agent._format_market_cap(25e9)
    assert "Milyon" in agent._format_market_cap(500e6)
    print("✅ Piyasa değeri formatlama testi başarılı")
