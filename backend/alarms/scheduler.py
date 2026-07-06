"""
FinanX — Alarm Zamanlayıcısı (APScheduler)
Her 5 dakikada bir fiyat ve KAP alarmlarını kontrol eder.
"""

import asyncio
from typing import Optional
from datetime import datetime
from loguru import logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import settings
from backend.alarms.alarm_db import alarm_repository
from backend.alarms.notifier import telegram_notifier
from backend.tools.live_price import live_price_service
from backend.tools.kap_watcher import kap_watcher
from backend.tools.sentiment import sentiment_analyzer
from backend.database.models import AlarmType


class AlarmScheduler:
    """
    APScheduler ile arka planda alarm kontrol görevi çalıştırır.
    """

    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._running = False

    def start(self):
        """Zamanlayıcıyı başlat."""
        if self._running:
            logger.warning("Zamanlayıcı zaten çalışıyor")
            return

        interval_minutes = settings.WATCHER_INTERVAL_MINUTES

        # Fiyat alarmı kontrolü
        self._scheduler.add_job(
            self.check_price_alarms,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="price_alarm_check",
            name="Fiyat Alarm Kontrolü",
            max_instances=1,
            coalesce=True,
        )

        # KAP bildirim kontrolü
        self._scheduler.add_job(
            self.check_kap_alarms,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="kap_alarm_check",
            name="KAP Alarm Kontrolü",
            max_instances=1,
            coalesce=True,
        )

        self._scheduler.start()
        self._running = True
        logger.success(
            f"✅ Alarm zamanlayıcısı başlatıldı "
            f"(her {interval_minutes} dakikada bir kontrol)"
        )

    def stop(self):
        """Zamanlayıcıyı durdur."""
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Alarm zamanlayıcısı durduruldu")

    async def check_price_alarms(self):
        """
        Aktif fiyat alarmlarını kontrol et.
        Eşik aşıldıysa Telegram bildirimi gönder.
        """
        logger.debug("Fiyat alarm kontrolü başlatılıyor...")

        try:
            active_alarms = await alarm_repository.list_active()
        except Exception as e:
            logger.error(f"Alarm listesi alınamadı: {e}")
            return

        # Fiyat alarmlarını filtrele
        price_alarms = [
            a for a in active_alarms
            if a.alarm_type in (
                AlarmType.PRICE_ABOVE,
                AlarmType.PRICE_BELOW,
                AlarmType.PERCENT_CHANGE,
            )
        ]

        if not price_alarms:
            return

        # Her hisse için benzersiz ticker listesi oluştur
        unique_tickers = list({a.ticker for a in price_alarms})

        # Toplu fiyat çekme
        prices = {}
        for ticker in unique_tickers:
            try:
                quote = live_price_service.get_quote(ticker)
                if not quote.get("error"):
                    prices[ticker] = quote
            except Exception as e:
                logger.warning(f"Fiyat çekme hatası {ticker}: {e}")

        # Her alarmı kontrol et
        for alarm in price_alarms:
            quote = prices.get(alarm.ticker)
            if not quote:
                continue

            current_price = quote.get("price", 0)
            change_pct = quote.get("change_pct", 0)
            triggered = False

            if alarm.alarm_type == AlarmType.PRICE_ABOVE:
                if current_price >= alarm.threshold_value:
                    triggered = True
                    await telegram_notifier.send_price_alert(
                        ticker=alarm.ticker,
                        current_price=current_price,
                        threshold=alarm.threshold_value,
                        direction="yukarı",
                        change_pct=change_pct,
                        chat_id=alarm.telegram_chat_id,
                    )

            elif alarm.alarm_type == AlarmType.PRICE_BELOW:
                if current_price <= alarm.threshold_value:
                    triggered = True
                    await telegram_notifier.send_price_alert(
                        ticker=alarm.ticker,
                        current_price=current_price,
                        threshold=alarm.threshold_value,
                        direction="aşağı",
                        change_pct=change_pct,
                        chat_id=alarm.telegram_chat_id,
                    )

            elif alarm.alarm_type == AlarmType.PERCENT_CHANGE:
                if abs(change_pct) >= abs(alarm.percent_threshold or 0):
                    triggered = True
                    await telegram_notifier.send_percent_alert(
                        ticker=alarm.ticker,
                        current_price=current_price,
                        change_pct=change_pct,
                        threshold_pct=alarm.percent_threshold,
                        chat_id=alarm.telegram_chat_id,
                    )

            if triggered:
                await alarm_repository.mark_triggered(alarm.id)
                logger.info(f"Alarm tetiklendi ve kapatıldı: ID={alarm.id} {alarm.ticker}")

    async def check_kap_alarms(self):
        """
        KAP bildirim alarmlarını kontrol et.
        Anahtar kelime eşleşmesi varsa duygu analizi yap ve bildir.
        """
        logger.debug("KAP alarm kontrolü başlatılıyor...")

        try:
            active_alarms = await alarm_repository.list_active()
        except Exception as e:
            logger.error(f"KAP alarm listesi alınamadı: {e}")
            return

        kap_alarms = [
            a for a in active_alarms
            if a.alarm_type == AlarmType.KAP_KEYWORD
        ]

        if not kap_alarms:
            return

        # Yeni KAP bildirimlerini çek
        new_notifications = kap_watcher.fetch_new_only()

        if not new_notifications:
            return

        logger.info(f"{len(new_notifications)} yeni KAP bildirimi bulundu")

        for alarm in kap_alarms:
            keyword = (alarm.kap_keyword or "").lower()
            ticker_filter = alarm.ticker

            for notification in new_notifications:
                # Ticker veya anahtar kelime eşleşmesi
                ticker_match = (
                    notification.ticker and
                    notification.ticker.upper() == ticker_filter.upper()
                )
                keyword_match = (
                    keyword and
                    keyword in notification.title.lower()
                )

                if not (ticker_match or keyword_match):
                    continue

                # Duygu analizi yap
                sentiment_result = await sentiment_analyzer.analyze(
                    text=notification.summary or notification.title,
                    ticker=notification.ticker,
                    title=notification.title,
                )

                # Telegram bildirimi gönder
                await telegram_notifier.send_kap_alert(
                    ticker=notification.ticker or alarm.ticker,
                    title=notification.title,
                    url=notification.url,
                    sentiment=sentiment_result.get("sentiment"),
                    summary=sentiment_result.get("summary"),
                    chat_id=alarm.telegram_chat_id,
                )

                logger.info(
                    f"KAP alarmı tetiklendi: {alarm.ticker} "
                    f"'{notification.title[:40]}'"
                )

    @property
    def is_running(self) -> bool:
        return self._running

    def get_jobs_info(self):
        """Çalışan görevlerin bilgisini döndür."""
        if not self._running:
            return []
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time),
            }
            for job in self._scheduler.get_jobs()
        ]


# Singleton
alarm_scheduler = AlarmScheduler()
