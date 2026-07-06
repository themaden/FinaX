"""
FinanX — Ana Streamlit Uygulaması
Piyasa genel bakış, RAG istatistikleri ve navigasyon.
"""

import streamlit as st
import requests
import asyncio
from datetime import datetime
from typing import Dict, Any

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))

from frontend.components.theme import apply_custom_theme

# ─── Sayfa Yapılandırması ──────────────────────────────────────────────────
st.set_page_config(
    page_title="FinanX — BIST AI Finansal Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Temayı uygula
apply_custom_theme()

BACKEND_URL = "http://localhost:8000"


def get_backend_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return r.status_code == 200, r.json()
    except Exception:
        return False, {}


def get_rag_stats():
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/documents/stats", timeout=2)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception:
        return {}


# ─── Verileri Yükle ─────────────────────────────────────────────────────────
is_healthy, health_data = get_backend_health()
rag_stats = get_rag_stats() if is_healthy else {}

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="finanx-logo">📈 FinanX</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**BIST AI Finansal Terminal**")
    st.markdown("*Yapay zeka destekli borsa analizi*")
    st.markdown("---")

    # Backend durumu (pulsing dot)
    if is_healthy:
        st.markdown(
            '<div style="display: flex; align-items: center; margin-bottom: 12px;">'
            '<span class="pulse-dot online"></span>'
            '<span style="font-weight: 600; color: #00d4aa;">Backend Bağlı</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display: flex; align-items: center; margin-bottom: 12px;">'
            '<span class="pulse-dot offline"></span>'
            '<span style="font-weight: 600; color: #ff4b4b;">Bağlantı Yok</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.info("Sistemi başlatmak için konsoldan backend'i çalıştırın.")

    st.markdown("---")
    st.markdown("**Hızlı Erişim**")
    st.page_link("pages/1_Chat.py", label="💬 AI Sohbet", icon="💬")
    st.page_link("pages/2_Analysis.py", label="📊 Hisse Analizi", icon="📊")
    st.page_link("pages/3_Portfolio.py", label="💼 Portföy", icon="💼")
    st.page_link("pages/4_Alarms.py", label="🔔 Alarmlar", icon="🔔")

    st.markdown("---")
    st.caption(f"FinanX Terminal v1.1 | {datetime.now().strftime('%d.%m.%Y')}")


# ─── Hero Başlık ─────────────────────────────────────────────────────────────
st.markdown('<div class="neon-title">FinanX</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="text-align: center; color: #94a3b8; font-size: 1.25rem; font-weight: 500; margin-bottom: 24px;">'
    'BIST Yapay Zeka Destekli Finansal Analiz ve RAG Platformu'
    '</div>',
    unsafe_allow_html=True,
)

# ─── Canlı İstatistikler Grid (Glass Cards) ──────────────────────────────────
st.markdown("---")
stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    total_vectors = rag_stats.get("total_vectors", 0)
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 20px;">
        <div style="font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">📚 İndekslenmiş Bilgi</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #00f2fe; margin-top: 8px;">{total_vectors:,} Parça</div>
        <div style="font-size: 0.75rem; color: #4e90ff; margin-top: 4px;">RAG Bilgi Bankası</div>
    </div>
    """, unsafe_allow_html=True)

with stat_col2:
    llm_provider = health_data.get("llm_provider", "Bilinmiyor").upper()
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 20px;">
        <div style="font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">🤖 Aktif Model</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #9b51e0; margin-top: 8px;">{llm_provider}</div>
        <div style="font-size: 0.75rem; color: #8892b0; margin-top: 4px;">Doğal Dil Analiz Motoru</div>
    </div>
    """, unsafe_allow_html=True)

with stat_col3:
    job_count = len(health_data.get("scheduler_jobs", [])) if is_healthy else 0
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 20px;">
        <div style="font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">🔔 Aktif Görevler</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #00d4aa; margin-top: 8px;">{job_count} Scheduler</div>
        <div style="font-size: 0.75rem; color: #00d4aa; margin-top: 4px;">KAP & Fiyat Dinleyici</div>
    </div>
    """, unsafe_allow_html=True)

with stat_col4:
    system_status = "STABİL" if is_healthy else "OFFLINE"
    status_color = "#00d4aa" if is_healthy else "#ff4b4b"
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 20px;">
        <div style="font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">📡 Sistem Durumu</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: {status_color}; margin-top: 8px;">{system_status}</div>
        <div style="font-size: 0.75rem; color: #8892b0; margin-top: 4px;">API Servis Bağlantısı</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Özellikler Grid ─────────────────────────────────────────────────────────
st.markdown("### 🛠️ Platform Özellikleri")
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

features = [
    ("💬", "AI Sohbet", "KAP faaliyet raporları ve bilançolarında semantik arama ve doğal dil sorgusu.", "pages/1_Chat.py"),
    ("🤖", "Çoklu Ajan", "Temel, teknik ve makroekonomi ajanlarının koordineli analiz raporu.", "pages/2_Analysis.py"),
    ("📡", "Canlı Veri", "BIST anlık borsa fiyatları, RSI, MACD ve hareketli ortalama indikatörleri.", "pages/2_Analysis.py"),
    ("🔔", "Akıllı Alarm", "Hisse fiyat eşikleri ve KAP anahtar kelimeleri için otomatik Telegram uyarıları.", "pages/4_Alarms.py"),
]

for col, (icon, title, desc, link) in zip([col_f1, col_f2, col_f3, col_f4], features):
    with col:
        st.markdown(f"""
        <div class="glass-card" style="min-height: 200px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 2.2rem; margin-bottom: 12px;">{icon}</div>
                <div style="font-weight: 700; color: #e2e8f0; font-size: 1.1rem; margin-bottom: 8px;">{title}</div>
                <div style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 16px;">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(link, label=f"Keşfet →", use_container_width=True)

# ─── Popüler BIST Hisseleri (Canlı veya Estetik Mock Fiyat Pilleri) ────────────
st.markdown("---")
st.markdown("### 📊 Popüler BIST Hisseleri")

POPULAR_TICKERS = {
    "THYAO": (285.40, 1.25),
    "EREGL": (52.30, -0.45),
    "AKBNK": (58.90, 2.10),
    "GARAN": (118.50, 0.75),
    "KCHOL": (212.10, -1.15),
    "BIMAS": (485.00, 1.85),
    "TUPRS": (164.30, -0.20),
    "TCELL": (94.75, 1.10)
}

ticker_cols = st.columns(len(POPULAR_TICKERS))

for col, (ticker, (mock_price, mock_change)) in zip(ticker_cols, POPULAR_TICKERS.items()):
    with col:
        price = mock_price
        change = mock_change

        # Canlı veri çekmeyi dene (hızlı timeout ile)
        if is_healthy:
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/v1/query",
                    json={"question": f"{ticker} fiyatı nedir", "session_id": "homepage_price"},
                    timeout=1.5,
                )
                if r.status_code == 200:
                    quote = r.json().get("metadata", {}).get("quote_data", {})
                    if quote and not quote.get("error"):
                        price = quote.get("price", price)
                        change = quote.get("change_pct", change)
            except Exception:
                pass

        badge_class = "badge-positive" if change >= 0 else "badge-negative"
        change_sign = "+" if change >= 0 else ""

        st.markdown(f"""
        <div class="glass-card" style="padding: 16px 12px; text-align: center; margin: 4px 0;">
            <div style="font-weight: 700; color: #4e90ff; font-size: 0.95rem; letter-spacing: 0.5px; margin-bottom: 6px;">{ticker}</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #e2e8f0; margin-bottom: 6px;">{price:.2f} TL</div>
            <span class="{badge_class}">{change_sign}{change:.2f}%</span>
        </div>
        """, unsafe_allow_html=True)

# ─── Hızlı Sorgulama Formu ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔍 AI Hızlı Finansal Sorgu")

with st.form("quick_query", clear_on_submit=False):
    query_col, btn_col = st.columns([6, 1])
    with query_col:
        quick_question = st.text_input(
            "Sorunuzu yazın",
            placeholder="Örn: THYAO bugünkü fiyatı nedir? veya EREGL son temettü ödemesi ne zaman?",
            label_visibility="collapsed",
        )
    with btn_col:
        submitted = st.form_submit_button("🔍 AI Sor", use_container_width=True)

if submitted and quick_question:
    with st.spinner("🤖 AI analiz ediliyor..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/query",
                json={"question": quick_question, "session_id": "homepage_query"},
                timeout=60,
            )
            if response.status_code == 200:
                data = response.json()
                route_labels = {
                    "live_price": "📡 Canlı Borsa Verisi",
                    "rag": "📚 Faaliyet Raporu & RAG",
                    "technical": "📈 Teknik İndikatör Analizi",
                    "multi_agent": "🤖 Çoklu Ajan Konsensüsü",
                    "kap": "📢 KAP Bildirim Analizi",
                    "compare": "⚖️ Şirket Karşılaştırması",
                }
                route_label = route_labels.get(data.get("route_type", ""), "🤖 AI Motoru")

                st.markdown(f"""
                <div class="glass-card" style="margin-top: 16px; border-left: 4px solid #00f2fe;">
                    <div style='color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;'>
                        {route_label} • {data.get('ticker', '') or 'GENEL'}
                    </div>
                    <div style='color: #e2e8f0; line-height: 1.8; font-size: 0.95rem;'>
                        {data.get('answer', '').replace(chr(10), '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"API Hatası: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Backend bağlantı hatası. Lütfen API'nin çalıştığından emin olun.")
        except Exception as e:
            st.error(f"Sorgu hatası: {str(e)}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #475569; font-size: 0.8rem; padding: 20px 0;'>
    FinanX Terminal v1.1 • BIST Yapay Zeka Finansal Analiz Platformu<br>
    <span style='color: #1e293b;'>Bu platform yatırım tavsiyesi niteliği taşımaz. Veriler bilgi amaçlı sunulmuştur.</span>
</div>
""", unsafe_allow_html=True)
