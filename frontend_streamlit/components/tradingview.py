"""
FinanX — TradingView Widget Bileşeni
"""

import streamlit as st
import streamlit.components.v1 as components


def tradingview_chart(
    ticker: str,
    exchange: str = "BIST",
    interval: str = "D",
    height: int = 500,
    theme: str = "dark",
):
    """
    TradingView canlı grafik widget'ı.

    Args:
        ticker: Hisse sembolü (örn: THYAO → BIST:THYAO)
        exchange: Borsa (varsayılan: BIST)
        interval: Zaman dilimi (1, 5, 15, 30, 60, D, W, M)
        height: Widget yüksekliği (piksel)
        theme: "dark" veya "light"
    """
    tv_symbol = f"{exchange}:{ticker.upper()}"
    bg_color = "#0e1117" if theme == "dark" else "#ffffff"
    text_color = "#d1d4dc" if theme == "dark" else "#131722"

    widget_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: {bg_color};
            }}
            .tradingview-widget-container {{
                width: 100%;
                height: {height}px;
            }}
        </style>
    </head>
    <body>
    <div class="tradingview-widget-container">
        <div id="tradingview_chart"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
            new TradingView.widget({{
                "width": "100%",
                "height": "{height}",
                "symbol": "{tv_symbol}",
                "interval": "{interval}",
                "timezone": "Europe/Istanbul",
                "theme": "{theme}",
                "style": "1",
                "locale": "tr",
                "toolbar_bg": "#131722",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "studies": [
                    "RSI@tv-basicstudies",
                    "MASimple@tv-basicstudies"
                ],
                "container_id": "tradingview_chart",
                "hide_top_toolbar": false,
                "save_image": true,
                "show_popup_button": true,
            }});
        </script>
    </div>
    </body>
    </html>
    """

    components.html(widget_html, height=height + 20, scrolling=False)


def tradingview_mini_chart(ticker: str, exchange: str = "BIST"):
    """Küçük fiyat özet widget'ı."""
    tv_symbol = f"{exchange}:{ticker.upper()}"

    mini_html = f"""
    <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script type="text/javascript"
            src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js">
        {{
            "symbol": "{tv_symbol}",
            "width": "100%",
            "height": "220",
            "locale": "tr",
            "dateRange": "12M",
            "colorTheme": "dark",
            "isTransparent": true,
            "autosize": true,
            "largeChartUrl": ""
        }}
        </script>
    </div>
    """

    components.html(mini_html, height=240, scrolling=False)
