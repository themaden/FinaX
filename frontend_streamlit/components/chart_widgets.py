"""
FinanX — Plotly Grafik Bileşenleri
Interaktif finansal grafikler.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np


DARK_COLORS = {
    "bg": "#0e1117",
    "surface": "#1e2130",
    "green": "#00d4aa",
    "red": "#ff4b4b",
    "blue": "#4e90ff",
    "yellow": "#ffd700",
    "text": "#d1d4dc",
    "grid": "#2d3147",
}


def price_chart_with_indicators(
    indicators: Dict[str, Any],
    ticker: str,
) -> go.Figure:
    """
    OHLCV + MA + Hacim + RSI + MACD multi-panel grafik.
    """
    history = indicators.get("price_history", {})
    dates = history.get("dates", [])
    prices = history.get("prices", [])
    sma20 = history.get("sma20", [])
    sma50 = history.get("sma50", [])
    volumes = history.get("volume", [])

    if not dates or not prices:
        return go.Figure()

    # 3 satır: Fiyat, Hacim, RSI
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.03,
        subplot_titles=[f"{ticker} Fiyat Grafiği", "Hacim", "RSI (14)"],
    )

    # ── Fiyat çizgisi ──────────────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=prices,
            name="Kapanış",
            line=dict(color=DARK_COLORS["blue"], width=2),
            fill="tozeroy",
            fillcolor="rgba(78, 144, 255, 0.08)",
        ),
        row=1,
        col=1,
    )

    # SMA20
    if sma20:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sma20,
                name="MA 20",
                line=dict(color=DARK_COLORS["yellow"], width=1.5, dash="dot"),
            ),
            row=1,
            col=1,
        )

    # SMA50
    if sma50:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sma50,
                name="MA 50",
                line=dict(color=DARK_COLORS["green"], width=1.5, dash="dash"),
            ),
            row=1,
            col=1,
        )

    # ── Hacim ───────────────────────────────────────────────────────────────
    if volumes:
        colors = [
            DARK_COLORS["green"] if i == 0 or prices[i] >= prices[i - 1]
            else DARK_COLORS["red"]
            for i in range(len(volumes))
        ]
        fig.add_trace(
            go.Bar(
                x=dates,
                y=volumes,
                name="Hacim",
                marker_color=colors,
                opacity=0.7,
            ),
            row=2,
            col=1,
        )

    # ── RSI ─────────────────────────────────────────────────────────────────
    rsi_val = indicators.get("rsi", {}).get("value")
    if rsi_val:
        # RSI zaman serisi oluştur (basit yaklaşım — sadece son değer)
        rsi_line = [None] * (len(dates) - 1) + [rsi_val]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=rsi_line,
                name=f"RSI ({rsi_val:.1f})",
                line=dict(color="#b24dff", width=2),
                connectgaps=False,
            ),
            row=3,
            col=1,
        )
        # Aşırı alım/satım bantları
        fig.add_hline(y=70, line_dash="dash", line_color=DARK_COLORS["red"],
                      opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color=DARK_COLORS["green"],
                      opacity=0.5, row=3, col=1)

    # ── Layout ──────────────────────────────────────────────────────────────
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_COLORS["bg"],
        plot_bgcolor=DARK_COLORS["surface"],
        font=dict(family="Inter, sans-serif", color=DARK_COLORS["text"]),
        height=600,
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor=DARK_COLORS["grid"],
            borderwidth=1,
        ),
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=40, b=0),
    )

    for i in range(1, 4):
        fig.update_xaxes(
            gridcolor=DARK_COLORS["grid"],
            row=i,
            col=1,
        )
        fig.update_yaxes(
            gridcolor=DARK_COLORS["grid"],
            row=i,
            col=1,
        )

    return fig


def portfolio_pie_chart(holdings: List[Dict[str, Any]]) -> go.Figure:
    """Portföy ağırlıkları pasta grafiği."""
    tickers = [h["ticker"] for h in holdings]
    weights = [h["weight_pct"] for h in holdings]
    pnls = [h["pnl_pct"] for h in holdings]

    colors = [DARK_COLORS["green"] if p >= 0 else DARK_COLORS["red"] for p in pnls]

    fig = go.Figure(
        go.Pie(
            labels=tickers,
            values=weights,
            hole=0.5,
            textinfo="label+percent",
            marker=dict(
                colors=px.colors.qualitative.Set3,
                line=dict(color=DARK_COLORS["bg"], width=2),
            ),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Ağırlık: %{value:.1f}%<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_COLORS["bg"],
        plot_bgcolor=DARK_COLORS["surface"],
        font=dict(family="Inter, sans-serif", color=DARK_COLORS["text"]),
        showlegend=True,
        height=400,
        title=dict(
            text="Portföy Dağılımı",
            font=dict(size=18, color=DARK_COLORS["text"]),
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        annotations=[
            dict(
                text="Portföy",
                x=0.5,
                y=0.5,
                font_size=18,
                showarrow=False,
                font_color=DARK_COLORS["text"],
            )
        ],
    )

    return fig


def portfolio_pnl_bar(holdings: List[Dict[str, Any]]) -> go.Figure:
    """Portföy K/Z bar grafiği."""
    tickers = [h["ticker"] for h in holdings]
    pnl_pcts = [h["pnl_pct"] for h in holdings]
    colors = [DARK_COLORS["green"] if p >= 0 else DARK_COLORS["red"] for p in pnl_pcts]

    fig = go.Figure(
        go.Bar(
            x=tickers,
            y=pnl_pcts,
            marker_color=colors,
            text=[f"%{p:+.2f}" for p in pnl_pcts],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>K/Z: %{y:.2f}%<extra></extra>",
        )
    )

    fig.add_hline(y=0, line_color=DARK_COLORS["text"], line_width=1, opacity=0.5)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_COLORS["bg"],
        plot_bgcolor=DARK_COLORS["surface"],
        font=dict(family="Inter, sans-serif", color=DARK_COLORS["text"]),
        height=350,
        title=dict(text="Kâr/Zarar Durumu (%)", font=dict(size=16)),
        yaxis=dict(ticksuffix="%", gridcolor=DARK_COLORS["grid"]),
        xaxis=dict(gridcolor=DARK_COLORS["grid"]),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    return fig


def comparison_radar_chart(
    comparison_data: Dict[str, Any],
    tickers: List[str],
) -> go.Figure:
    """Hisse karşılaştırma radar grafiği."""
    categories = ["F/K", "PD/DD", "52H Konumu", "Temettü", "Volatilite"]

    fig = go.Figure()

    colors = [DARK_COLORS["blue"], DARK_COLORS["green"], DARK_COLORS["yellow"]]

    for i, ticker in enumerate(tickers[:3]):
        data = comparison_data.get(ticker, {}).get("quote", {})
        pe = min(data.get("pe_ratio") or 0, 50) / 50 * 10
        pb = min(data.get("pb_ratio") or 0, 10) / 10 * 10
        high = data.get("52w_high", 1)
        low = data.get("52w_low", 0)
        price = data.get("price", (high + low) / 2)
        position = (price - low) / (high - low) * 10 if high != low else 5
        div = (data.get("dividend_yield") or 0) * 100

        values = [pe, pb, position, div, 5]  # Volatilite placeholder

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill="toself",
                name=ticker,
                line_color=colors[i % len(colors)],
                fillcolor=colors[i % len(colors)].replace(")", ", 0.15)").replace("rgb", "rgba"),
                opacity=0.8,
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                gridcolor=DARK_COLORS["grid"],
                tickfont=dict(color=DARK_COLORS["text"]),
            ),
            angularaxis=dict(
                gridcolor=DARK_COLORS["grid"],
                tickfont=dict(color=DARK_COLORS["text"]),
            ),
            bgcolor=DARK_COLORS["surface"],
        ),
        template="plotly_dark",
        paper_bgcolor=DARK_COLORS["bg"],
        font=dict(family="Inter, sans-serif", color=DARK_COLORS["text"]),
        height=400,
        title=dict(text="Karşılaştırma Radar Grafiği", font=dict(size=16)),
        showlegend=True,
        margin=dict(l=0, r=0, t=50, b=0),
    )

    return fig
