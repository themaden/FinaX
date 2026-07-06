"""
FinanX — /portfolio Endpoint
Portföy risk analizi ve Beta hesaplama.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import asyncio
import numpy as np
import pandas as pd
from loguru import logger

from backend.tools.live_price import live_price_service, get_historical_async
from backend.llm_factory import get_llm

router = APIRouter()


class PortfolioHoldingInput(BaseModel):
    ticker: str
    shares: float = Field(..., gt=0)
    avg_cost: float = Field(..., gt=0)


class PortfolioRequest(BaseModel):
    holdings: List[PortfolioHoldingInput]
    benchmark: str = Field(default="XU100", description="Kıyaslama endeksi")


PORTFOLIO_PROMPT = """Sen bir risk yönetimi uzmanısın. Kullanıcının portföyünü analiz et.

Aşağıdaki metrikleri değerlendir:
1. Portföy çeşitlendirmesi (hisse sayısı ve ağırlık dağılımı)
2. Sektör konsantrasyonu riskleri
3. Genel risk seviyesi (Düşük/Orta/Yüksek)
4. Öneriler

Tüm yanıtı Türkçe ver."""


@router.post("/portfolio")
async def analyze_portfolio(request: PortfolioRequest):
    """
    Portföy risk analizi yap.

    - Toplam değer ve kâr/zarar hesaplama
    - Her hissenin portföy ağırlığı
    - Beta katsayısı (benchmark'a göre)
    - Çeşitlendirme puanı
    - LLM risk değerlendirmesi
    """
    holdings = request.holdings
    if not holdings:
        raise HTTPException(status_code=400, detail="Portföy boş")

    # 1. Anlık fiyatları çek
    tickers = [h.ticker.upper() for h in holdings]
    quotes = {}
    for ticker in tickers:
        try:
            q = live_price_service.get_quote(ticker)
            if not q.get("error"):
                quotes[ticker] = q
        except Exception as e:
            logger.warning(f"Portföy fiyat hatası {ticker}: {e}")

    # 2. Portföy hesaplamaları
    portfolio_items = []
    total_current_value = 0.0
    total_cost_value = 0.0

    for holding in holdings:
        ticker = holding.ticker.upper()
        quote = quotes.get(ticker, {})
        current_price = quote.get("price", holding.avg_cost)

        current_value = holding.shares * current_price
        cost_value = holding.shares * holding.avg_cost
        pnl = current_value - cost_value
        pnl_pct = (pnl / cost_value * 100) if cost_value > 0 else 0

        portfolio_items.append({
            "ticker": ticker,
            "shares": holding.shares,
            "avg_cost": holding.avg_cost,
            "current_price": current_price,
            "current_value": round(current_value, 2),
            "cost_value": round(cost_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "sector": quote.get("sector"),
            "pe_ratio": quote.get("pe_ratio"),
        })

        total_current_value += current_value
        total_cost_value += cost_value

    # 3. Ağırlıkları hesapla
    for item in portfolio_items:
        item["weight_pct"] = round(
            (item["current_value"] / total_current_value * 100)
            if total_current_value > 0 else 0,
            2,
        )

    # 4. Çeşitlendirme puanı (Herfindahl-Hirschman endeksi tersi)
    weights = [item["weight_pct"] / 100 for item in portfolio_items]
    hhi = sum(w**2 for w in weights)
    diversification_score = round((1 - hhi) * 100, 1)

    # 5. Beta hesaplama (BIST100'e karşı)
    portfolio_betas = await _calculate_portfolio_beta(tickers, weights)

    # 6. LLM risk analizi
    context = _build_portfolio_context(portfolio_items, total_current_value, total_cost_value)
    risk_analysis = await _get_llm_risk_analysis(context)

    return {
        "summary": {
            "total_current_value": round(total_current_value, 2),
            "total_cost": round(total_cost_value, 2),
            "total_pnl": round(total_current_value - total_cost_value, 2),
            "total_pnl_pct": round(
                (total_current_value - total_cost_value) / total_cost_value * 100
                if total_cost_value > 0 else 0,
                2,
            ),
            "diversification_score": diversification_score,
            "portfolio_beta": portfolio_betas.get("portfolio_beta"),
            "holding_count": len(holdings),
        },
        "holdings": portfolio_items,
        "risk_analysis": risk_analysis,
        "betas": portfolio_betas,
    }


async def _calculate_portfolio_beta(tickers: List[str], weights: List[float]) -> dict:
    """Her hisse için Beta hesapla (BIST100'e karşı)."""
    try:
        bist100_df = await get_historical_async("^XU100", period="1y", interval="1d")

        betas = {}
        portfolio_beta = 0.0

        for ticker, weight in zip(tickers, weights):
            df = await get_historical_async(ticker, period="1y", interval="1d")
            beta = _compute_beta(df, bist100_df)
            betas[ticker] = round(beta, 3) if beta is not None else None
            if beta is not None:
                portfolio_beta += beta * weight

        return {
            "individual_betas": betas,
            "portfolio_beta": round(portfolio_beta, 3),
            "interpretation": _interpret_beta(portfolio_beta),
        }
    except Exception as e:
        logger.warning(f"Beta hesaplama hatası: {e}")
        return {"individual_betas": {}, "portfolio_beta": None, "interpretation": "Hesaplanamadı"}


def _compute_beta(
    stock_df: Optional[pd.DataFrame],
    market_df: Optional[pd.DataFrame],
) -> Optional[float]:
    """Tek hisse için Beta hesapla."""
    if stock_df is None or market_df is None:
        return None
    if not isinstance(stock_df, pd.DataFrame) or not isinstance(market_df, pd.DataFrame):
        return None
    if stock_df.empty or market_df.empty:
        return None
    try:
        # Sütun adlarını düzleştir
        if isinstance(stock_df.columns, pd.MultiIndex):
            stock_df = stock_df.copy()
            stock_df.columns = stock_df.columns.get_level_values(0)
        if isinstance(market_df.columns, pd.MultiIndex):
            market_df = market_df.copy()
            market_df.columns = market_df.columns.get_level_values(0)

        if "Close" not in stock_df.columns or "Close" not in market_df.columns:
            return None

        stock_ret = stock_df["Close"].squeeze().pct_change().dropna()
        market_ret = market_df["Close"].squeeze().pct_change().dropna()

        common_dates = stock_ret.index.intersection(market_ret.index)
        if len(common_dates) < 30:
            return None

        s = stock_ret.loc[common_dates].values
        m = market_ret.loc[common_dates].values

        covariance = np.cov(s, m)[0, 1]
        market_variance = np.var(m)
        if market_variance <= 0:
            return None
        return float(covariance / market_variance)
    except Exception as e:
        logger.debug(f"Beta hesaplama exception: {e}")
        return None


def _interpret_beta(beta: Optional[float]) -> str:
    if beta is None:
        return "Hesaplanamadı"
    if beta < 0.5:
        return "Düşük risk — piyasadan az etkilenir"
    elif beta < 1.0:
        return "Orta risk — piyasadan az duyarlı"
    elif beta < 1.5:
        return "Orta-yüksek risk — piyasayla birlikte hareket eder"
    else:
        return "Yüksek risk — piyasadan fazla duyarlı, volatil"


def _build_portfolio_context(
    items: list,
    total_val: float,
    total_cost: float,
) -> str:
    lines = [
        f"PORTFÖY ÖZET: Toplam Değer {total_val:,.2f} TL | "
        f"Maliyet {total_cost:,.2f} TL\n",
    ]
    for item in items:
        lines.append(
            f"- {item['ticker']}: %{item['weight_pct']} ağırlık | "
            f"K/Z: %{item['pnl_pct']:+.2f} | "
            f"Sektör: {item.get('sector', 'N/A')}"
        )
    return "\n".join(lines)


async def _get_llm_risk_analysis(context: str) -> str:
    try:
        messages = [
            {"role": "system", "content": PORTFOLIO_PROMPT},
            {"role": "user", "content": context},
        ]
        llm = get_llm()
        response = await llm.ainvoke(messages)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        return f"Risk analizi alınamadı: {str(e)}"
