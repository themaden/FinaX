"""
FinanX — AI Sohbet Sayfası
Yapay zeka ile interaktif finansal sohbet arayüzü.
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="FinanX — AI Sohbet",
    page_icon="💬",
    layout="wide",
)

BACKEND_URL = st.session_state.get("backend_url", "http://localhost:8000")
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from frontend.components.theme import apply_custom_theme

# Temayı uygula
apply_custom_theme()

# CSS
st.markdown("""
<style>
    .chat-message-user {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(79, 172, 254, 0.25) 100%);
        border: 1px solid rgba(0, 242, 254, 0.35);
        border-radius: 16px 16px 4px 16px;
        padding: 16px 20px;
        margin: 12px 0;
        color: #e2e8f0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 20px rgba(0, 242, 254, 0.08);
        animation: slideIn 0.3s ease;
    }

    .chat-message-assistant {
        background: rgba(22, 28, 51, 0.55);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px 16px 16px 4px;
        padding: 16px 20px;
        margin: 12px 0;
        color: #e2e8f0;
        max-width: 90%;
        box-shadow: 0 6px 30px rgba(0, 0, 0, 0.35);
        animation: slideIn 0.3s ease;
    }

    .route-badge {
        display: inline-block;
        background: rgba(79, 172, 254, 0.15);
        border: 1px solid rgba(79, 172, 254, 0.3);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.72rem;
        color: #00f2fe;
        margin-bottom: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .source-chip {
        display: inline-block;
        background: rgba(13, 17, 33, 0.7);
        border: 1px solid rgba(78, 144, 255, 0.15);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.72rem;
        color: #94a3b8;
        margin: 4px 2px 0 2px;
        transition: all 0.2s;
    }
    
    .source-chip:hover {
        border-color: #00f2fe;
        color: #e2e8f0;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .thinking-indicator {
        display: flex;
        gap: 6px;
        padding: 18px 24px;
        background: rgba(22, 28, 51, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin: 12px 0;
        max-width: 140px;
        justify-content: center;
        align-items: center;
    }

    .thinking-dot {
        width: 8px;
        height: 8px;
        background: #00f2fe;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    
    .thinking-dot:nth-child(1) { animation-delay: -0.32s; }
    .thinking-dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())[:8]

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💬 AI Sohbet")
    st.markdown("---")

    st.markdown("**Örnek Sorular**")

    example_questions = [
        "📡 THYAO bugünkü fiyatı nedir?",
        "📈 EREGL teknik analizi",
        "🤖 AKBNK kapsamlı analiz yap",
        "📚 THY 2023 net kârı nedir?",
        "📢 Son KAP bildirimleri",
        "🔍 KCHOL ile SAHOL karşılaştır",
    ]

    for q in example_questions:
        if st.button(q, use_container_width=True, key=f"example_{q[:20]}"):
            st.session_state.pending_question = q.split(" ", 1)[1]
            st.rerun()

    st.markdown("---")

    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Oturum ID:** `{st.session_state.session_id}`")
    st.markdown(f"**Mesaj Sayısı:** {len(st.session_state.messages)}")

# ─── Ana İçerik ──────────────────────────────────────────────────────────────
st.markdown("## 💬 FinanX AI Sohbet")
st.caption("BIST hakkında her şeyi sorun — Türkçe konuşuyor, Türk borsasını biliyor")
st.markdown("---")

# Mesaj geçmişini göster
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align: center; padding: 60px 20px; color: #374151;'>
            <div style='font-size: 3rem; margin-bottom: 16px;'>🤖</div>
            <div style='font-size: 1.2rem; font-weight: 600; color: #4e90ff;
                        margin-bottom: 8px;'>Merhaba! Ben FinanX AI</div>
            <div style='font-size: 0.95rem; line-height: 1.7;'>
                BIST hisseleri hakkında sorularınızı yanıtlayabilirim.<br>
                Canlı fiyatlar, teknik analiz, faaliyet raporları ve daha fazlası...<br>
                <b style='color: #00d4aa;'>Sol menüden örnek sorulardan başlayabilirsiniz.</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        route = msg.get("route_type", "")
        sources = msg.get("sources", [])
        timestamp = msg.get("timestamp", "")

        if role == "user":
            st.markdown(f"""
            <div class="chat-message-user">
                <div style='font-size: 0.85rem; color: #8892b0; margin-bottom: 6px;'>
                    👤 Siz • {timestamp}
                </div>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            route_labels = {
                "live_price": "📡 Canlı Veri",
                "rag": "📚 Belge Araması",
                "technical": "📈 Teknik Analiz",
                "multi_agent": "🤖 Çoklu Ajan Analizi",
                "kap": "📢 KAP Bildirimleri",
                "compare": "⚖️ Karşılaştırma",
            }
            route_label = route_labels.get(route, "🤖 AI")

            sources_html = ""
            if sources:
                chips = "".join(
                    f'<span class="source-chip">📄 {s.get("filename", "belge")[:25]}</span>'
                    for s in sources[:3]
                )
                sources_html = f'<div style="margin-top: 10px;">{chips}</div>'

            st.markdown(f"""
            <div class="chat-message-assistant">
                <span class="route-badge">{route_label}</span>
                <div style='line-height: 1.8;'>{content.replace(chr(10), '<br>')}</div>
                {sources_html}
                <div style='font-size: 0.72rem; color: #374151; margin-top: 8px;'>{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── Pending Soru (Örnek butonlardan) ────────────────────────────────────────
pending_q = st.session_state.pop("pending_question", None)

# ─── Chat Input ──────────────────────────────────────────────────────────────
user_input = st.chat_input(
    "BIST hakkında bir şey sorun... (Örn: THYAO'nun RSI değeri nedir?)"
)

# Pending veya yeni soru
question = pending_q or user_input

if question:
    timestamp = datetime.now().strftime("%H:%M")

    # Kullanıcı mesajını ekle
    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "timestamp": timestamp,
    })

    # AI yanıtı al
    with st.spinner("🤖 FinanX AI düşünüyor..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/query",
                json={
                    "question": question,
                    "session_id": st.session_state.session_id,
                },
                timeout=120,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("answer", "Yanıt alınamadı."),
                    "route_type": data.get("route_type", ""),
                    "sources": data.get("sources", []),
                    "indicators": data.get("indicators"),
                    "ticker": data.get("ticker"),
                    "timestamp": datetime.now().strftime("%H:%M"),
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ API hatası: {response.status_code}",
                    "timestamp": timestamp,
                })
        except requests.exceptions.ConnectionError:
            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    "❌ **Backend'e bağlanılamadı.**\n\n"
                    "Lütfen şu komutu çalıştırın:\n"
                    "```bash\n"
                    "cd FinanX && python -m uvicorn backend.api.main:app --reload\n"
                    "```"
                ),
                "timestamp": timestamp,
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Hata: {str(e)}",
                "timestamp": timestamp,
            })

    st.rerun()
