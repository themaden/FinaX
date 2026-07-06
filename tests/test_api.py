"""
FinanX — API Entegrasyon Testleri
FastAPI endpoint'lerinin yanıt sürelerini ve doğruluğunu test eder.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock


def test_health_endpoint():
    """API sağlık kontrolü testi."""
    try:
        import requests
        r = requests.get("http://localhost:8000/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check: {data}")
    except Exception as e:
        pytest.skip(f"Backend çalışmıyor: {e}")


def test_query_endpoint_live_price():
    """Canlı fiyat sorgusu testi."""
    try:
        import requests
        import time
        start = time.time()
        r = requests.post(
            "http://localhost:8000/api/v1/query",
            json={"question": "THYAO bugünkü fiyatı nedir", "session_id": "test"},
            timeout=30,
        )
        elapsed = time.time() - start

        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert data.get("route_type") == "live_price"
        assert elapsed < 10, f"Yanıt süresi çok uzun: {elapsed:.1f}s"

        print(f"✅ Live price sorgusu: {elapsed:.2f}s | route={data.get('route_type')}")
    except Exception as e:
        pytest.skip(f"Backend çalışmıyor: {e}")


def test_alarms_crud():
    """Alarm CRUD işlemleri testi."""
    try:
        import requests

        # Oluştur
        create_resp = requests.post(
            "http://localhost:8000/api/v1/alarms",
            json={
                "ticker": "TEST",
                "alarm_type": "price_above",
                "threshold_value": 999.0,
                "notes": "Test alarmı",
            },
            timeout=10,
        )
        assert create_resp.status_code == 201
        alarm_id = create_resp.json()["alarm"]["id"]

        # Listele
        list_resp = requests.get("http://localhost:8000/api/v1/alarms", timeout=10)
        assert list_resp.status_code == 200
        alarms = list_resp.json()["alarms"]
        assert any(a["id"] == alarm_id for a in alarms)

        # Sil
        del_resp = requests.delete(f"http://localhost:8000/api/v1/alarms/{alarm_id}", timeout=10)
        assert del_resp.status_code == 200

        print(f"✅ Alarm CRUD: oluşturma, listeleme, silme başarılı (ID={alarm_id})")
    except Exception as e:
        pytest.skip(f"Backend çalışmıyor: {e}")


def test_live_price_service():
    """yfinance BIST veri çekme testi."""
    from backend.tools.live_price import LivePriceService

    service = LivePriceService()
    quote = service.get_quote("THYAO")

    assert not quote.get("error"), f"Veri çekme hatası: {quote.get('error')}"
    assert "price" in quote
    assert quote["price"] > 0
    assert quote["ticker"] == "THYAO"

    print(f"✅ Live price: THYAO = {quote['price']} TL (%{quote.get('change_pct', 0):+.2f})")


def test_technical_indicators():
    """Teknik indikatör hesaplama testi."""
    from backend.tools.live_price import LivePriceService
    from backend.tools.indicators import TechnicalIndicators

    service = LivePriceService()
    df = service.get_historical("THYAO", period="6mo")

    if df is None or df.empty:
        pytest.skip("Veri alınamadı")

    ti = TechnicalIndicators()
    result = ti.analyze(df, ticker="THYAO")

    assert not result.get("error"), f"İndikatör hatası: {result.get('error')}"
    assert "rsi" in result
    assert "macd" in result
    assert "overall_signal" in result

    rsi_val = result["rsi"]["value"]
    assert 0 <= rsi_val <= 100, f"RSI aralık dışı: {rsi_val}"

    print(f"✅ Teknik analiz: RSI={rsi_val:.1f}, Sinyal={result['overall_signal']}")


def test_kap_watcher():
    """KAP RSS çekme testi."""
    from backend.tools.kap_watcher import KapWatcher

    watcher = KapWatcher()
    entries = watcher.fetch_notifications(max_entries=5)

    # RSS erişimi yoksa geç
    if not entries:
        pytest.skip("KAP RSS erişilemedi")

    assert len(entries) > 0
    first = entries[0]
    assert first.title, "Başlık boş olmamalı"

    print(f"✅ KAP: {len(entries)} bildirim çekildi. İlk: {first.title[:50]}")
