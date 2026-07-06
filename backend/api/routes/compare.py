"""
FinanX — /compare Endpoint
İki BIST hissesini yan yana karşılaştıran analiz.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from backend.tools.live_price import live_price_service
from backend.tools.indicators import technical_indicators
from backend.tools.live_price import get_historical_async
from backend.llm_factory import get_llm

import asyncio

router = APIRouter()


class CompareRequest(BaseModel):
    tickers: List[str] = Field(..., min_length=2, max_length=5, description="Karşılaştırılacak hisseler")
    period: str = Field(default="6mo", description="Teknik analiz periyodu")


COMPARE_PROMPT = """Sen bir BIST analiz uzmanısın. İki hisseyi karşılaştırarak yatırımcılar için
kapsamlı bir karşılaştırma raporu hazırla.

KARŞILAŞTIRMA KRİTERLERİ:
1. Değerleme: F/K, PD/DD oranları
2. Fiyat Performansı: Son 52 hafta düşük/yüksek
3. Piyasa Değeri
4. Teknik Görünüm: RSI ve trend
5. Genel Değerlendirme: Hangisi daha cazip görünüyor ve neden?

Tüm yanıtı Türkçe ver, tablo formatı kullan."""


@router.post("/compare")
async def compare_stocks(request: CompareRequest):
    """
    İki veya daha fazla hisseyi karşılaştır.

    - Anlık fiyat ve rasyolar
    - Teknik indikatörler
    - LLM karşılaştırma yorumu
    """
    tickers = [t.upper() for t in request.tickers[:5]]
    logger.info(f"Karşılaştırma: {tickers}")

    # Her hisse için veri topla
    results = {}

    async def fetch_data(ticker: str):
        quote = live_price_service.get_quote(ticker)
        df = await get_historical_async(ticker, period=request.period)
        tech = {}
        if df is not None and not df.empty:
            tech = technical_indicators.analyze(df, ticker)
        return ticker, quote, tech

    try:
        fetched = await asyncio.gather(
            *[fetch_data(t) for t in tickers],
            return_exceptions=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    comparison_data = {}
    for item in fetched:
        if isinstance(item, Exception):
            continue
        ticker, quote, tech = item
        comparison_data[ticker] = {
            "quote": quote,
            "technical": {
                "rsi": tech.get("rsi"),
                "overall_signal": tech.get("overall_signal"),
                "moving_averages": tech.get("moving_averages"),
            } if tech else {},
        }

    # LLM ile karşılaştırma yorumu
    context = "KARŞILAŞTIRMA VERİLERİ:\n\n"
    for ticker, data in comparison_data.items():
        q = data["quote"]
        t = data["technical"]
        context += (
            f"## {ticker}\n"
            f"Fiyat: {q.get('price', 'N/A')} TL | "
            f"Değişim: %{q.get('change_pct', 0):+.2f} | "
            f"F/K: {q.get('pe_ratio', 'N/A')} | "
            f"PD/DD: {q.get('pb_ratio', 'N/A')}\n"
            f"Piyasa Değeri: {q.get('market_cap', 'N/A')}\n"
            f"52H Aralık: {q.get('52w_low', 'N/A')} - {q.get('52w_high', 'N/A')} TL\n"
            f"RSI: {t.get('rsi', {}).get('value', 'N/A')} | "
            f"Teknik Sinyal: {t.get('overall_signal', 'N/A')}\n\n"
        )

    messages = [
        {"role": "system", "content": COMPARE_PROMPT},
        {"role": "user", "content": f"Şu hisseleri karşılaştır: {', '.join(tickers)}\n\n{context}"},
    ]

    try:
        llm = get_llm()
        response = await llm.ainvoke(messages)
        comparison_text = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        logger.error(f"Karşılaştırma LLM hatası: {e}")
        comparison_text = "LLM karşılaştırma yorumu alınamadı."

    return {
        "tickers": tickers,
        "comparison_data": comparison_data,
        "analysis": comparison_text,
    }
