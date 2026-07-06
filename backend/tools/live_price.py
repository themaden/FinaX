"""
FinanX — Canlı Borsa Fiyat Araçları (yfinance)
BIST hisselerinin anlık fiyat, hacim ve temel rasyolarını getirir.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import numpy as np
from loguru import logger


# BIST sembolü → yfinance formatı dönüşümü
def to_yf_symbol(ticker: str) -> str:
    """
    THYAO → THYAO.IS, EREGL → EREGL.IS
    Zaten .IS içeriyorsa değiştirme.
    """
    ticker = ticker.upper().strip()
    if not ticker.endswith(".IS"):
        return f"{ticker}.IS"
    return ticker


def from_yf_symbol(ticker: str) -> str:
    """THYAO.IS → THYAO"""
    return ticker.upper().replace(".IS", "")


class LivePriceService:
    """
    yfinance üzerinden BIST hisse verilerini çeken servis.
    Tüm metodlar sync'tir; FastAPI async ortamında
    asyncio.to_thread ile çağrılır.
    """

    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """
        Anlık fiyat, günlük değişim, hacim ve temel rasyolar.

        Returns:
            {
                "ticker": "THYAO",
                "price": 285.40,
                "change": 3.20,
                "change_pct": 1.14,
                "volume": 15_234_000,
                "market_cap": 98_500_000_000,
                "pe_ratio": 8.5,
                "pb_ratio": 1.2,
                "52w_high": 310.00,
                "52w_low": 185.00,
                "currency": "TRY",
                "timestamp": "2024-01-15T14:30:00"
            }
        """
        yf_symbol = to_yf_symbol(ticker)
        clean_ticker = from_yf_symbol(ticker)

        try:
            stock = yf.Ticker(yf_symbol)
            info = stock.info

            if not info or info.get("regularMarketPrice") is None:
                # Hızlı veri dene
                fast_info = stock.fast_info
                price = getattr(fast_info, "last_price", None)
                prev_close = getattr(fast_info, "previous_close", None)
                volume = getattr(fast_info, "three_month_average_volume", None)

                if price is None:
                    return {"error": f"{clean_ticker} için veri bulunamadı"}

                change = (price - prev_close) if prev_close else 0
                change_pct = (change / prev_close * 100) if prev_close else 0

                return {
                    "ticker": clean_ticker,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": int(volume) if volume else 0,
                    "market_cap": getattr(fast_info, "market_cap", None),
                    "pe_ratio": None,
                    "pb_ratio": None,
                    "52w_high": getattr(fast_info, "year_high", None),
                    "52w_low": getattr(fast_info, "year_low", None),
                    "currency": "TRY",
                    "timestamp": datetime.now().isoformat(),
                }

            price = info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose", price)
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

            return {
                "ticker": clean_ticker,
                "name": info.get("longName", clean_ticker),
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": info.get("regularMarketVolume", 0),
                "avg_volume": info.get("averageVolume", 0),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "currency": info.get("currency", "TRY"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Fiyat çekme hatası {ticker}: {e}")
            return {"error": str(e), "ticker": clean_ticker}

    def get_historical(
        self,
        ticker: str,
        period: str = "6mo",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Tarihsel OHLCV verisini DataFrame olarak döndür.

        Args:
            ticker: Hisse sembolü
            period: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"
            interval: "1m", "5m", "15m", "1h", "1d", "1wk", "1mo"

        Returns:
            pd.DataFrame: [Date, Open, High, Low, Close, Volume]
        """
        yf_symbol = to_yf_symbol(ticker)
        try:
            df = yf.download(
                yf_symbol,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
            )
            if df.empty:
                logger.warning(f"Tarihsel veri boş: {ticker}")
            return df
        except Exception as e:
            logger.error(f"Tarihsel veri hatası {ticker}: {e}")
            return pd.DataFrame()

    def get_multiple_quotes(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Birden fazla hisse için anlık fiyat getir."""
        results = {}
        for ticker in tickers:
            results[ticker] = self.get_quote(ticker)
        return results

    def get_financials(self, ticker: str) -> Dict[str, Any]:
        """
        Yıllık finansal tablolar: gelir tablosu, bilanço, nakit akışı.
        """
        yf_symbol = to_yf_symbol(ticker)
        clean_ticker = from_yf_symbol(ticker)

        try:
            stock = yf.Ticker(yf_symbol)

            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow

            def df_to_dict(df: pd.DataFrame) -> Dict:
                if df is None or df.empty:
                    return {}
                # Sayısal değerleri JSON uyumlu hale getir
                result = {}
                for col in df.columns:
                    col_str = str(col.date()) if hasattr(col, 'date') else str(col)
                    result[col_str] = {}
                    for idx in df.index:
                        val = df.loc[idx, col]
                        if pd.isna(val):
                            result[col_str][str(idx)] = None
                        else:
                            result[col_str][str(idx)] = round(float(val), 2)
                return result

            return {
                "ticker": clean_ticker,
                "income_statement": df_to_dict(income_stmt),
                "balance_sheet": df_to_dict(balance_sheet),
                "cash_flow": df_to_dict(cash_flow),
            }
        except Exception as e:
            logger.error(f"Finansal tablo hatası {ticker}: {e}")
            return {"error": str(e), "ticker": clean_ticker}

    def search_ticker(self, company_name: str) -> List[Dict[str, str]]:
        """Şirket adından BIST sembolü bul."""
        # Yaygın BIST hisseleri ve alternatif isimleri
        BIST_COMPANIES = {
            "türk hava yolları": "THYAO", "thy": "THYAO", "turkish airlines": "THYAO",
            "ereğli": "EREGL", "erdemir": "EREGL",
            "akbank": "AKBNK", "garanti": "GARAN", "garanti bankası": "GARAN",
            "yapı kredi": "YKBNK", "iş bankası": "ISCTR", "halkbank": "HALKB",
            "koç holding": "KCHOL", "sabancı": "SAHOL",
            "vestel": "VESTL", "arçelik": "ARCLK",
            "bim": "BIMAS", "migros": "MGROS",
            "tüpraş": "TUPRS", "togg": "TOGG",
            "enka": "ENKAI", "tekfen": "TKFEN",
            "ülker": "ULKER", "anadolu efes": "AEFES",
            "petkim": "PETKM", "tav": "TAVHL",
            "turkcell": "TCELL", "türk telekom": "TTKOM",
            "alarko": "ALARK", "logo": "LOGO",
        }

        query = company_name.lower().strip()
        matches = []
        for name, symbol in BIST_COMPANIES.items():
            if query in name or name in query or query in symbol.lower():
                matches.append({"name": name.title(), "ticker": symbol})

        return matches[:5]


# Async wrapper
async def get_quote_async(ticker: str) -> Dict[str, Any]:
    """Async ortamda canlı fiyat çek."""
    service = LivePriceService()
    return await asyncio.to_thread(service.get_quote, ticker)


async def get_historical_async(
    ticker: str,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """Async ortamda tarihsel veri çek."""
    service = LivePriceService()
    return await asyncio.to_thread(service.get_historical, ticker, period, interval)


# Singleton
live_price_service = LivePriceService()
