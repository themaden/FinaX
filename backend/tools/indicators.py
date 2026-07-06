"""
FinanX — Teknik İndikatörler
RSI, Hareketli Ortalama, MACD, Bollinger Bantları hesaplama.
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger


class TechnicalIndicators:
    """
    OHLCV DataFrame'i alıp teknik indikatörleri hesaplayan sınıf.
    'ta' kütüphanesini ve saf pandas/numpy kullanır.
    """

    @staticmethod
    def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index (RSI) hesapla."""
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.round(2)

    @staticmethod
    def calculate_macd(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD hesapla.
        Returns: (macd_line, signal_line, histogram)
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line.round(4), signal_line.round(4), histogram.round(4)

    @staticmethod
    def calculate_bollinger(
        close: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bantları hesapla.
        Returns: (upper_band, middle_band, lower_band)
        """
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper.round(2), middle.round(2), lower.round(2)

    @staticmethod
    def calculate_sma(close: pd.Series, period: int) -> pd.Series:
        """Basit Hareketli Ortalama (SMA)."""
        return close.rolling(window=period).mean().round(2)

    @staticmethod
    def calculate_ema(close: pd.Series, period: int) -> pd.Series:
        """Üstel Hareketli Ortalama (EMA)."""
        return close.ewm(span=period, adjust=False).mean().round(2)

    @staticmethod
    def calculate_support_resistance(
        df: pd.DataFrame,
        window: int = 20,
    ) -> Dict[str, float]:
        """Yakın destek ve direnç seviyelerini hesapla."""
        if df.empty or len(df) < window:
            return {}

        recent = df.tail(window)
        current_price = df["Close"].iloc[-1]

        # Yerel minimum (destek) ve maksimum (direnç) seviyeleri
        highs = recent["High"].nlargest(3).tolist()
        lows = recent["Low"].nsmallest(3).tolist()

        support_levels = [l for l in lows if l < current_price]
        resistance_levels = [h for h in highs if h > current_price]

        return {
            "support": round(support_levels[0], 2) if support_levels else round(recent["Low"].min(), 2),
            "resistance": round(resistance_levels[0], 2) if resistance_levels else round(recent["High"].max(), 2),
            "current_price": round(float(current_price), 2),
        }

    def analyze(self, df: pd.DataFrame, ticker: str = "") -> Dict[str, Any]:
        """
        DataFrame'den tüm teknik indikatörleri hesapla ve yorumla.

        Args:
            df: OHLCV DataFrame (yfinance çıktısı)
            ticker: Log için hisse sembolü

        Returns:
            Dict: Tüm indikatörler ve yorumları
        """
        if df is None or df.empty or len(df) < 30:
            return {"error": "Yeterli tarihsel veri yok (minimum 30 gün gerekli)"}

        # Sütun adlarını düzleştir (MultiIndex varsa)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        low = df["Low"].squeeze()
        volume = df["Volume"].squeeze()

        current_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])

        # RSI
        rsi = self.calculate_rsi(close)
        current_rsi = float(rsi.iloc[-1]) if not rsi.isna().all() else None

        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(close)
        current_macd = float(macd_line.iloc[-1]) if not macd_line.isna().all() else None
        current_signal = float(signal_line.iloc[-1]) if not signal_line.isna().all() else None
        current_hist = float(histogram.iloc[-1]) if not histogram.isna().all() else None

        # Hareketli Ortalamalar
        sma20 = self.calculate_sma(close, 20)
        sma50 = self.calculate_sma(close, 50)
        ema20 = self.calculate_ema(close, 20)

        # Bollinger Bantları
        bb_upper, bb_mid, bb_lower = self.calculate_bollinger(close)

        # Destek/Direnç
        levels = self.calculate_support_resistance(df)

        # --- Teknik Yorumlar ---
        signals = []
        bullish_count = 0
        bearish_count = 0

        # RSI yorumu
        rsi_signal = "nötr"
        if current_rsi:
            if current_rsi < 30:
                rsi_signal = "aşırı satım (alım fırsatı olabilir)"
                bullish_count += 1
                signals.append(f"RSI {current_rsi:.1f}: Aşırı Satım ✅")
            elif current_rsi > 70:
                rsi_signal = "aşırı alım (dikkatli olun)"
                bearish_count += 1
                signals.append(f"RSI {current_rsi:.1f}: Aşırı Alım ⚠️")
            else:
                signals.append(f"RSI {current_rsi:.1f}: Normal bölge")

        # MACD yorumu
        if current_macd is not None and current_hist is not None:
            if current_hist > 0 and current_macd > current_signal:
                bullish_count += 1
                signals.append("MACD: Yükseliş sinyali 📈")
            elif current_hist < 0:
                bearish_count += 1
                signals.append("MACD: Düşüş sinyali 📉")

        # MA yorumu
        sma20_val = float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else None
        sma50_val = float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else None

        if sma20_val and sma50_val:
            if sma20_val > sma50_val:
                bullish_count += 1
                signals.append(f"MA20 ({sma20_val:.2f}) > MA50 ({sma50_val:.2f}): Yükseliş trendi 📈")
            else:
                bearish_count += 1
                signals.append(f"MA20 ({sma20_val:.2f}) < MA50 ({sma50_val:.2f}): Düşüş trendi 📉")

        # Genel sinyal
        if bullish_count > bearish_count:
            overall_signal = "YÜKSELEN 📈"
        elif bearish_count > bullish_count:
            overall_signal = "DÜŞEN 📉"
        else:
            overall_signal = "YATAY ➡️"

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "price_change_pct": round((current_price - prev_price) / prev_price * 100, 2),
            "rsi": {
                "value": round(current_rsi, 2) if current_rsi else None,
                "signal": rsi_signal,
            },
            "macd": {
                "macd": round(current_macd, 4) if current_macd else None,
                "signal": round(current_signal, 4) if current_signal else None,
                "histogram": round(current_hist, 4) if current_hist else None,
            },
            "moving_averages": {
                "sma_20": sma20_val,
                "sma_50": sma50_val,
                "ema_20": float(ema20.iloc[-1]) if not pd.isna(ema20.iloc[-1]) else None,
            },
            "bollinger": {
                "upper": float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
                "middle": float(bb_mid.iloc[-1]) if not pd.isna(bb_mid.iloc[-1]) else None,
                "lower": float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
            },
            "support_resistance": levels,
            "signals": signals,
            "overall_signal": overall_signal,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            # Grafik için son 60 günlük kapanış
            "price_history": {
                "dates": [str(d.date()) for d in close.tail(60).index],
                "prices": close.tail(60).round(2).tolist(),
                "sma20": sma20.tail(60).round(2).tolist(),
                "sma50": sma50.tail(60).round(2).tolist(),
                "volume": volume.tail(60).astype(int).tolist(),
            },
        }


# Singleton
technical_indicators = TechnicalIndicators()
