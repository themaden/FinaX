"""
FinanX — Portföy Risk Analizi Sayfası
"""

import streamlit as st
import requests
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from frontend.components.chart_widgets import portfolio_pie_chart, portfolio_pnl_bar

st.set_page_config(page_title="FinanX — Portföy", page_icon="💼", layout="wide")
BACKEND_URL = "http://localhost:8000"

from frontend.components.theme import apply_custom_theme

# Temayı uygula
apply_custom_theme()

st.markdown("## 💼 Portföy Risk Analizi")
st.caption("Hisselerinizi ekleyin, AI risk değerlendirmesi ve Beta analizi yapsın")

# ─── Portföy Girişi ────────────────────────────────────────────────────────────
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"ticker": "THYAO", "shares": 100, "avg_cost": 250.0},
        {"ticker": "AKBNK", "shares": 500, "avg_cost": 45.0},
        {"ticker": "EREGL", "shares": 200, "avg_cost": 80.0},
    ]

st.markdown("### 📝 Portföy Girişi")

with st.expander("➕ Hisse Ekle / Düzenle", expanded=True):
    df = pd.DataFrame(st.session_state.portfolio)
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "ticker": st.column_config.TextColumn("Hisse Sembolü", width="small"),
            "shares": st.column_config.NumberColumn("Adet", min_value=1, format="%.0f"),
            "avg_cost": st.column_config.NumberColumn("Ort. Maliyet (TL)", min_value=0.01, format="%.2f"),
        },
        use_container_width=True,
    )

    if st.button("📊 Portföyü Analiz Et", type="primary", use_container_width=True):
        holdings = [
            {"ticker": row["ticker"].upper(), "shares": row["shares"], "avg_cost": row["avg_cost"]}
            for _, row in edited_df.iterrows()
            if row.get("ticker") and row.get("shares") and row.get("avg_cost")
        ]
        st.session_state.portfolio = holdings
        st.session_state.portfolio_result = None

        with st.spinner("💼 Portföy analiz ediliyor..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/api/v1/portfolio",
                    json={"holdings": holdings},
                    timeout=60,
                )
                if resp.status_code == 200:
                    st.session_state.portfolio_result = resp.json()
                else:
                    st.error(f"API hatası: {resp.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Backend'e bağlanılamadı")
            except Exception as e:
                st.error(f"Hata: {str(e)}")

# ─── Sonuçlar ──────────────────────────────────────────────────────────────────
result = st.session_state.get("portfolio_result")

if result:
    summary = result.get("summary", {})
    holdings = result.get("holdings", [])
    betas = result.get("betas", {})

    st.markdown("---")
    st.markdown("### 📊 Portföy Özeti")

    col1, col2, col3, col4, col5 = st.columns(5)
    total_val = summary.get("total_current_value", 0)
    total_pnl = summary.get("total_pnl", 0)
    total_pnl_pct = summary.get("total_pnl_pct", 0)
    div_score = summary.get("diversification_score", 0)
    beta = summary.get("portfolio_beta")

    with col1:
        st.metric("💰 Toplam Değer", f"{total_val:,.0f} TL")
    with col2:
        st.metric(
            "📈 Toplam K/Z",
            f"{total_pnl:+,.0f} TL",
            f"%{total_pnl_pct:+.2f}",
        )
    with col3:
        st.metric("🎲 Çeşitlendirme", f"%{div_score:.1f}", help="100% = Mükemmel çeşitlendirme")
    with col4:
        st.metric("⚡ Portföy Beta", f"{beta:.2f}" if beta else "N/A")
    with col5:
        risk_level = "🟢 Düşük" if div_score > 70 else "🟡 Orta" if div_score > 40 else "🔴 Yüksek"
        st.metric("⚖️ Risk Seviyesi", risk_level)

    st.markdown("---")
    st.markdown("### 📈 Görsel Analiz")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_pie = portfolio_pie_chart(holdings)
        st.plotly_chart(fig_pie, use_container_width=True)
    with chart_col2:
        fig_bar = portfolio_pnl_bar(holdings)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tablo
    st.markdown("### 📋 Detaylı Pozisyonlar")
    display_df = pd.DataFrame([
        {
            "Hisse": h["ticker"],
            "Adet": h["shares"],
            "Ort. Maliyet": f"{h['avg_cost']:.2f} TL",
            "Anlık Fiyat": f"{h['current_price']:.2f} TL",
            "Değer": f"{h['current_value']:,.0f} TL",
            "K/Z": f"{h['pnl']:+,.0f} TL",
            "K/Z %": f"%{h['pnl_pct']:+.2f}",
            "Ağırlık": f"%{h['weight_pct']:.1f}",
            "Beta": betas.get("individual_betas", {}).get(h["ticker"], "N/A"),
        }
        for h in holdings
    ])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🤖 AI Risk Değerlendirmesi")
    risk_analysis = result.get("risk_analysis", "")
    if risk_analysis:
        st.markdown(risk_analysis)

else:
    st.info("Portföyünüzü girin ve **📊 Portföyü Analiz Et** butonuna tıklayın")
