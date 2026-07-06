"""
FinanX — Hisse Analizi Sayfası
TradingView grafik + Plotly indikatörler + Çoklu ajan analizi.
"""

import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="FinanX — Hisse Analizi",
    page_icon="📊",
    layout="wide",
)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from frontend.components.tradingview import tradingview_chart
from frontend.components.chart_widgets import price_chart_with_indicators

BACKEND_URL = "http://localhost:8000"

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from frontend.components.theme import apply_custom_theme

# Temayı uygula
apply_custom_theme()

st.markdown("""
<style>
    .metric-card {
        background: rgba(22, 28, 51, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Hisse Analizi")
    st.markdown("---")

    ticker = st.text_input(
        "Hisse Sembolü",
        value="THYAO",
        placeholder="THYAO, EREGL, AKBNK...",
        help="BIST hisse sembolünü girin (büyük harf)",
    ).upper().strip()

    period = st.selectbox(
        "Zaman Periyodu",
        options=["1mo", "3mo", "6mo", "1y", "2y"],
        index=2,
        format_func=lambda x: {
            "1mo": "1 Ay", "3mo": "3 Ay", "6mo": "6 Ay",
            "1y": "1 Yıl", "2y": "2 Yıl"
        }[x],
    )

    interval = st.selectbox(
        "Grafik İnterval",
        options=["D", "W", "60", "15", "5"],
        index=0,
        format_func=lambda x: {
            "D": "Günlük", "W": "Haftalık",
            "60": "Saatlik", "15": "15 Dakika", "5": "5 Dakika"
        }[x],
    )

    st.markdown("---")

    analyze_btn = st.button("🔍 Analiz Başlat", use_container_width=True, type="primary")
    full_analysis_btn = st.button("🤖 Tam Ajan Analizi", use_container_width=True)

# ─── Ana İçerik ──────────────────────────────────────────────────────────────
st.markdown(f"## 📊 {ticker} Analizi")

if not ticker:
    st.info("Sol menüden bir hisse sembolü girin")
    st.stop()

# ─── Anlık Fiyat Metrikleri ───────────────────────────────────────────────────
with st.spinner(f"📡 {ticker} verileri yükleniyor..."):
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/query",
            json={"question": f"{ticker} fiyatı", "session_id": "analysis"},
            timeout=15,
        )
        quote_data = response.json().get("metadata", {}).get("quote_data", {}) if response.status_code == 200 else {}
    except Exception:
        quote_data = {}

if quote_data and not quote_data.get("error"):
    price = quote_data.get("price", 0)
    change_pct = quote_data.get("change_pct", 0)
    change = quote_data.get("change", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Fiyat", f"{price:.2f} TL", f"{change:+.2f} TL")
    with col2:
        st.metric("📊 Değişim", f"%{change_pct:+.2f}")
    with col3:
        st.metric("📦 Hacim", f"{quote_data.get('volume', 0):,}")
    with col4:
        st.metric("📈 F/K", quote_data.get("pe_ratio") or "N/A")
    with col5:
        st.metric("📉 PD/DD", quote_data.get("pb_ratio") or "N/A")

st.markdown("---")

# ─── Sekmeler ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 TradingView", "📊 Teknik Analiz", "🤖 Ajan Raporu", "📢 KAP"
])

# TAB 1: TradingView
with tab1:
    st.markdown("### 📈 Canlı Grafik (TradingView)")
    tradingview_chart(ticker=ticker, interval=interval, height=550, theme="dark")

# TAB 2: Teknik Analiz
with tab2:
    st.markdown("### 📊 Teknik Analiz")
    if analyze_btn or True:
        with st.spinner("Teknik indikatörler hesaplanıyor..."):
            try:
                tech_resp = requests.post(
                    f"{BACKEND_URL}/api/v1/query",
                    json={
                        "question": f"{ticker} RSI MACD teknik analiz",
                        "session_id": "technical",
                    },
                    timeout=30,
                )
                if tech_resp.status_code == 200:
                    tech_data = tech_resp.json()
                    indicators = tech_data.get("indicators")

                    if indicators and not indicators.get("error"):
                        # Sinyal kartları
                        sig_col1, sig_col2, sig_col3 = st.columns(3)
                        with sig_col1:
                            rsi_val = indicators.get("rsi", {}).get("value", "N/A")
                            rsi_signal = indicators.get("rsi", {}).get("signal", "")
                            st.metric("RSI (14)", rsi_val, rsi_signal)
                        with sig_col2:
                            st.metric(
                                "Genel Sinyal",
                                indicators.get("overall_signal", "N/A"),
                            )
                        with sig_col3:
                            bb = indicators.get("bollinger", {})
                            st.metric(
                                "BB Üst/Alt",
                                f"{bb.get('upper', 'N/A'):.2f}" if bb.get('upper') else "N/A",
                                f"Alt: {bb.get('lower', 'N/A'):.2f}" if bb.get('lower') else None,
                            )

                        # Grafik
                        fig = price_chart_with_indicators(indicators, ticker)
                        st.plotly_chart(fig, use_container_width=True)

                        # Sinyaller
                        st.markdown("#### 📋 Sinyal Özeti")
                        for signal in indicators.get("signals", []):
                            if "📈" in signal or "✅" in signal:
                                st.success(signal)
                            elif "📉" in signal or "⚠️" in signal:
                                st.warning(signal)
                            else:
                                st.info(signal)
                    else:
                        st.markdown(tech_data.get("answer", ""))
            except requests.exceptions.ConnectionError:
                st.error("Backend'e bağlanılamadı")

# TAB 3: Çoklu Ajan Raporu
with tab3:
    st.markdown("### 🤖 Çoklu Ajan Kapsamlı Analizi")
    st.caption("Temel + Teknik + Makro ajanların koordineli analizi")

    if full_analysis_btn:
        with st.spinner("🤖 Çoklu ajan analizi başlatılıyor... (30-60 saniye sürebilir)"):
            try:
                agent_resp = requests.post(
                    f"{BACKEND_URL}/api/v1/query",
                    json={
                        "question": f"{ticker} hakkında kapsamlı yatırım analizi yap",
                        "session_id": "agent_analysis",
                    },
                    timeout=120,
                )
                if agent_resp.status_code == 200:
                    agent_data = agent_resp.json()
                    signal = agent_data.get("metadata", {}).get("signal", "NÖTR")

                    signal_colors = {
                        "OLUMLU": "success",
                        "OLUMSUZ": "error",
                        "NÖTR": "info",
                    }
                    getattr(st, signal_colors.get(signal, "info"))(
                        f"Genel Değerlendirme: **{signal}**"
                    )
                    st.markdown(agent_data.get("answer", "Analiz alınamadı."))
                else:
                    st.error(f"API hatası: {agent_resp.status_code}")
            except Exception as e:
                st.error(f"Hata: {str(e)}")
    else:
        st.info(
            "Sol menüden **🤖 Tam Ajan Analizi** butonuna tıklayarak "
            "4 uzman AI ajanın kapsamlı analizini başlatın."
        )

# TAB 4: KAP Bildirimleri
with tab4:
    st.markdown("### 📢 KAP Bildirimleri")
    with st.spinner(f"{ticker} KAP bildirimleri yükleniyor..."):
        try:
            kap_resp = requests.post(
                f"{BACKEND_URL}/api/v1/query",
                json={
                    "question": f"{ticker} son KAP bildirimleri nelerdir",
                    "session_id": "kap",
                },
                timeout=30,
            )
            if kap_resp.status_code == 200:
                kap_data = kap_resp.json()
                st.markdown(kap_data.get("answer", "KAP verisi bulunamadı."))
            else:
                st.warning("KAP bildirimleri alınamadı")
        except requests.exceptions.ConnectionError:
            st.error("Backend'e bağlanılamadı")
