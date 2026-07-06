"""
FinanX — Alarm Yönetimi Sayfası
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="FinanX — Alarmlar", page_icon="🔔", layout="wide")
BACKEND_URL = "http://localhost:8000"

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from frontend.components.theme import apply_custom_theme

# Temayı uygula
apply_custom_theme()

st.markdown("""
<style>
    .alarm-card {
        background: rgba(22, 28, 51, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        margin: 10px 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🔔 Alarm Yönetimi")
st.caption("Fiyat eşiği veya KAP kelime alarmlarını kurun, Telegram'dan anında bildirim alın")

tab1, tab2, tab3 = st.tabs(["➕ Yeni Alarm", "📋 Alarmlarım", "⚙️ Telegram Ayarları"])

# ─── Yeni Alarm ────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### ➕ Yeni Alarm Oluştur")

    with st.form("new_alarm"):
        col1, col2 = st.columns(2)

        with col1:
            ticker = st.text_input("Hisse Sembolü", placeholder="THYAO, EREGL...", value="THYAO").upper()
            alarm_type = st.selectbox(
                "Alarm Türü",
                options=["price_above", "price_below", "percent_change", "kap_keyword"],
                format_func=lambda x: {
                    "price_above": "📈 Fiyat Eşiğin Üzerine Çıktı",
                    "price_below": "📉 Fiyat Eşiğin Altına Düştü",
                    "percent_change": "📊 Yüzdesel Değişim",
                    "kap_keyword": "📢 KAP Anahtar Kelime",
                }[x],
            )

        with col2:
            threshold = st.number_input("Fiyat Eşiği (TL)", min_value=0.0, value=0.0, step=0.5)
            percent_thresh = st.number_input("Yüzde Eşiği (%)", min_value=0.0, value=0.0, step=0.5)
            kap_keyword = st.text_input("KAP Anahtar Kelime", placeholder="temettü, sözleşme...")

        telegram_chat = st.text_input(
            "Telegram Chat ID (opsiyonel)",
            placeholder="Boş bırakırsanız config'deki ID kullanılır",
        )
        notes = st.text_area("Not", placeholder="Bu alarm için açıklama...")

        submitted = st.form_submit_button("🔔 Alarm Oluştur", type="primary", use_container_width=True)

        if submitted and ticker:
            payload = {
                "ticker": ticker,
                "alarm_type": alarm_type,
                "threshold_value": threshold if threshold > 0 else None,
                "percent_threshold": percent_thresh if percent_thresh > 0 else None,
                "kap_keyword": kap_keyword or None,
                "telegram_chat_id": telegram_chat or None,
                "notes": notes or None,
            }
            try:
                resp = requests.post(f"{BACKEND_URL}/api/v1/alarms", json=payload, timeout=10)
                if resp.status_code == 201:
                    st.success(f"✅ {ticker} alarmı başarıyla oluşturuldu!")
                else:
                    st.error(f"Hata: {resp.json()}")
            except requests.exceptions.ConnectionError:
                st.error("Backend'e bağlanılamadı")

# ─── Alarmlarım ────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 📋 Mevcut Alarmlar")

    col_refresh, col_filter = st.columns([3, 1])
    with col_filter:
        active_only = st.checkbox("Sadece aktif", value=True)

    try:
        resp = requests.get(
            f"{BACKEND_URL}/api/v1/alarms",
            params={"active_only": active_only},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            alarms = data.get("alarms", [])

            if not alarms:
                st.info("Henüz alarm kurulmamış. İlk alarmı oluşturmak için sol sekmeye geçin.")
            else:
                st.markdown(f"**Toplam: {data.get('total', 0)} alarm**")
                for alarm in alarms:
                    type_labels = {
                        "price_above": "📈 Fiyat Üst",
                        "price_below": "📉 Fiyat Alt",
                        "percent_change": "📊 Yüzde",
                        "kap_keyword": "📢 KAP",
                    }
                    status = "🟢 Aktif" if alarm["is_active"] else "⚫ Pasif"
                    alarm_type_label = type_labels.get(alarm["alarm_type"], alarm["alarm_type"])

                    with st.container():
                        acol1, acol2, acol3, acol4 = st.columns([2, 2, 2, 1])
                        with acol1:
                            st.markdown(f"**{alarm['ticker']}** — {alarm_type_label}")
                        with acol2:
                            threshold_str = (
                                f"Eşik: {alarm.get('threshold_value')} TL"
                                if alarm.get("threshold_value")
                                else f"Kelime: {alarm.get('kap_keyword', '')}"
                                if alarm.get("kap_keyword")
                                else f"%{alarm.get('percent_threshold')} değişim"
                            )
                            st.caption(threshold_str)
                        with acol3:
                            st.caption(status)
                        with acol4:
                            if st.button("🗑️", key=f"del_{alarm['id']}", help="Sil"):
                                del_resp = requests.delete(
                                    f"{BACKEND_URL}/api/v1/alarms/{alarm['id']}",
                                    timeout=10,
                                )
                                if del_resp.status_code == 200:
                                    st.success("Silindi")
                                    st.rerun()
                        st.divider()
        else:
            st.error(f"API hatası: {resp.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Backend'e bağlanılamadı")

# ─── Telegram Ayarları ─────────────────────────────────────────────────────────
with tab3:
    st.markdown("### ⚙️ Telegram Bot Kurulumu")

    st.markdown("""
    **Adımlar:**
    1. Telegram'da [@BotFather](https://t.me/botfather) ile konuşun
    2. `/newbot` komutunu gönderin ve bir isim belirleyin
    3. Aldığınız **Bot Token**'ı `.env` dosyasına ekleyin: `TELEGRAM_BOT_TOKEN=...`
    4. [@userinfobot](https://t.me/userinfobot) ile **Chat ID**'nizi öğrenin
    5. `.env` dosyasına ekleyin: `TELEGRAM_CHAT_ID=...`
    """)

    col_test1, col_test2 = st.columns(2)
    with col_test1:
        test_chat_id = st.text_input("Test Chat ID (opsiyonel)", placeholder="Boş bırakırsanız config kullanılır")

    with col_test2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📨 Test Bildirimi Gönder", use_container_width=True):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/api/v1/alarms/test-telegram",
                    params={"chat_id": test_chat_id or None},
                    timeout=15,
                )
                if resp.status_code == 200:
                    st.success("✅ Telegram bağlantısı başarılı! Mesajı kontrol edin.")
                else:
                    st.error(f"❌ Hata: {resp.json().get('detail', 'Bilinmeyen hata')}")
            except requests.exceptions.ConnectionError:
                st.error("Backend'e bağlanılamadı")
