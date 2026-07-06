# FinanX — BIST AI Finansal Analiz Platformu

<div align="center">

```
 _____ _             _   _  __  
|  ___(_)_ __   __ _| \ | |/ /_  
| |_  | | '_ \ / _` |  \| | '_ \ 
|  _| | | | | | (_| | |\  | (_) |
|_|   |_|_| |_|\__,_|_| \_|\___/ 
```

**Türkiye Borsası (BIST) Yapay Zeka Finansal Analiz Platformu**

RAG • Multi-Agent AI • Canlı Borsa • Telegram Alarmları

</div>

---

## 🚀 Özellikler

| Özellik | Açıklama |
|---------|----------|
| 💬 **AI Sohbet** | KAP raporlarında Türkçe doğal dil sorgusu |
| 🤖 **Çoklu Ajan** | 4 uzman AI ajanın koordineli analizi |
| 📡 **Canlı Veri** | BIST anlık fiyat, RSI, MACD, Bollinger |
| 📚 **RAG** | FAISS + Sentence-Transformers ile belge arama |
| 🔔 **Akıllı Alarm** | Fiyat eşiği ve KAP kelime Telegram bildirimi |
| 📈 **TradingView** | Canlı grafik widget entegrasyonu |
| 💼 **Portföy** | Beta, çeşitlendirme, K/Z analizi |
| 📢 **KAP** | RSS bildirimi + LLM duygu analizi |

---

## 📁 Proje Yapısı

```
FinanX/
├── backend/
│   ├── api/routes/        # FastAPI endpoint'leri
│   ├── rag/               # RAG modülü (FAISS)
│   ├── agents/            # Çoklu ajan sistemi
│   ├── tools/             # Borsa araçları
│   ├── alarms/            # Telegram alarm sistemi
│   └── database/          # SQLAlchemy modelleri
├── frontend/
│   ├── app.py             # Ana Streamlit sayfası
│   ├── pages/             # 4 ayrı sayfa
│   └── components/        # TradingView, Plotly
├── data/
│   ├── reports/           # PDF faaliyet raporları
│   └── faiss_index/       # Vektör veri tabanı
├── tests/                 # Pytest test paketi
└── docker/                # Docker konteynerları
```

---

## ⚡ Hızlı Başlangıç

### 1. Ortam Hazırlığı

```bash
# Python sanal ortam
python -m venv venv
venv\Scripts\activate   # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. API Anahtarları

`.env.example` dosyasını kopyalayın:

```bash
copy .env.example .env
```

`.env` dosyasını düzenleyin:

```env
# En az bir LLM sağlayıcısı gerekli:
GOOGLE_API_KEY=your_key_here        # Gemini (önerilen)
# veya
OPENAI_API_KEY=your_key_here        # GPT-4o

LLM_PROVIDER=google                 # "google" veya "openai"

# Telegram alarmları için (opsiyonel):
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Backend Başlatma

```bash
# Kök dizinde çalıştırın:
python -m uvicorn backend.api.main:app --reload --port 8000
```

API Swagger Docs: http://localhost:8000/docs

### 4. Frontend Başlatma

```bash
streamlit run frontend/app.py
```

Arayüz: http://localhost:8501

---

## 📄 PDF Rapor Yükleme (RAG)

Faaliyet raporlarını veya KAP bildirimlerini sisteme ekleyin:

```bash
# data/reports/ klasörüne kopyalayın:
THYAO_2023_faaliyet.pdf
EREGL_2023_Q4.pdf
```

Veya Streamlit arayüzünden drag-and-drop ile yükleyin.

---

## 🤖 Ajan Mimarisi

```
Kullanıcı Sorusu
      │
      ▼
  [LLM Router]
  ┌────┴────┐
  │         │
  ▼         ▼
[RAG]   [Live Veri]
  │         │
  └────┬────┘
       │
       ▼
[Multi-Agent Orchestrator]
  ├── Temel Analiz Ajanı
  ├── Teknik Analiz Ajanı
  ├── Makro Analiz Ajanı
  └── Raporlama Ajanı
       │
       ▼
  Türkçe Rapor
```

---

## 🔔 Alarm Sistemi

```json
# Fiyat alarmı: THYAO 300 TL'nin üzerine çıkınca bildir
POST /api/v1/alarms
{
    "ticker": "THYAO",
    "alarm_type": "price_above",
    "threshold_value": 300.0
}

# KAP kelime alarmı: Temettü haberi gelince bildir
{
    "ticker": "EREGL",
    "alarm_type": "kap_keyword",
    "kap_keyword": "temettü"
}
```

---

## 🐳 Docker ile Dağıtım

```bash
# Docker Compose ile tüm servisleri başlat
docker compose -f docker/docker-compose.yml up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:8501
```

---

## 🧪 Testler

```bash
# Tüm testleri çalıştır
pytest tests/ -v

# Belirli test kategorisi
pytest tests/test_rag.py -v      # RAG testleri
pytest tests/test_api.py -v      # API testleri (backend gerekir)
pytest tests/test_agents.py -v   # Ajan testleri
```

---

## ⚠️ Yasal Uyarı

Bu platform **yalnızca bilgi amaçlıdır** ve yatırım tavsiyesi niteliği taşımaz. BIST'te yapılan yatırımlar zarar riski içerir. Yatırım kararlarınızda bir finans danışmanına başvurunuz.

---

## 📝 Lisans

MIT License — Özgürce kullanın, geliştirin ve katkıda bulunun.
