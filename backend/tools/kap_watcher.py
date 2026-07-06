"""
FinanX — KAP RSS Dinleyici
kap.org.tr RSS beslemelerini periyodik olarak kontrol eder.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import feedparser
from loguru import logger


# KAP RSS Besleme URL'leri
KAP_RSS_URLS = {
    "genel": "https://www.kap.org.tr/tr/rss/bildirim",
    "onemli": "https://www.kap.org.tr/tr/rss/ozet",
}


class KapEntry:
    """Tek bir KAP bildirimi."""

    def __init__(self, entry: Any):
        # feedparser entry nesnesi — attribute erişimi ile
        self.title: str = getattr(entry, "title", "") or ""
        self.url: str = getattr(entry, "link", "") or ""
        self.summary: str = getattr(entry, "summary", "") or ""
        self.published_at: Optional[datetime] = self._parse_date(entry)
        self.ticker: Optional[str] = self._extract_ticker()

    def _parse_date(self, entry: Any) -> Optional[datetime]:
        """Yayın tarihini parse et."""
        try:
            # feedparser zaten parsed_time verir
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                import time
                ts = time.mktime(entry.published_parsed)
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            # String olarak dene
            if hasattr(entry, "published") and entry.published:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(entry.published)
        except Exception:
            pass
        return None

    def _extract_ticker(self) -> Optional[str]:
        """Başlıktan hisse sembolünü çıkarmaya çalış."""
        # KAP bildirimi formatı: "THYAO - Özel Durum Açıklaması"
        if " - " in self.title:
            potential = self.title.split(" - ")[0].strip().upper()
            if 3 <= len(potential) <= 6 and potential.isalpha():
                return potential
        # "[THYAO]" formatı
        import re
        match = re.search(r'\[([A-Z]{3,6})\]', self.title.upper())
        if match:
            return match.group(1)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "ticker": self.ticker,
        }

    def __repr__(self):
        return f"<KapEntry {self.ticker} {self.title[:40]}>"


class KapWatcher:
    """
    KAP bildirimlerini periyodik olarak çeken ve filtreleyen servis.
    """

    def __init__(self):
        self._seen_urls: set = set()

    def fetch_notifications(
        self,
        max_entries: int = 50,
        ticker_filter: Optional[str] = None,
    ) -> List[KapEntry]:
        """
        KAP RSS beslemesinden son bildirimleri çek.

        Args:
            max_entries: Maksimum bildirim sayısı
            ticker_filter: Belirli bir hisseye filtrele

        Returns:
            List[KapEntry]: Bildirim listesi
        """
        entries: List[KapEntry] = []

        for feed_name, url in KAP_RSS_URLS.items():
            try:
                logger.debug(f"KAP RSS çekiliyor: {url}")

                feed = feedparser.parse(
                    url,
                    request_headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36"
                        )
                    }
                )

                if feed.bozo and not feed.entries:
                    logger.warning(
                        f"KAP RSS parse hatası ({feed_name}): "
                        f"{getattr(feed, 'bozo_exception', 'bilinmiyor')}"
                    )
                    continue

                for raw_entry in feed.entries[:max_entries]:
                    entry = KapEntry(raw_entry)

                    # Tekrar gönderimi filtrele
                    if entry.url and entry.url in self._seen_urls:
                        continue

                    # Ticker filtresi
                    if ticker_filter and entry.ticker:
                        if entry.ticker.upper() != ticker_filter.upper():
                            continue

                    entries.append(entry)

            except Exception as e:
                logger.error(f"KAP besleme hatası ({feed_name}): {e}")
                continue

        # Tarihe göre sırala (en yeni önce)
        def sort_key(x: KapEntry) -> datetime:
            if x.published_at:
                # timezone-aware ise UTC'ye çevir
                if x.published_at.tzinfo is not None:
                    return x.published_at
                return x.published_at.replace(tzinfo=timezone.utc)
            return datetime.min.replace(tzinfo=timezone.utc)

        entries.sort(key=sort_key, reverse=True)

        logger.info(f"KAP: {len(entries)} bildirim çekildi")
        return entries

    def mark_seen(self, entries: List[KapEntry]):
        """İşlenen bildirimleri 'görüldü' olarak işaretle."""
        for entry in entries:
            if entry.url:
                self._seen_urls.add(entry.url)

        # Bellek yönetimi
        if len(self._seen_urls) > 10000:
            self._seen_urls.clear()

    def fetch_new_only(
        self,
        ticker_filter: Optional[str] = None,
    ) -> List[KapEntry]:
        """Sadece daha önce görülmemiş bildirimleri getir."""
        all_entries = self.fetch_notifications(ticker_filter=ticker_filter)
        new_entries = [e for e in all_entries if e.url not in self._seen_urls]
        self.mark_seen(new_entries)
        return new_entries

    def get_notifications_for_ticker(
        self,
        ticker: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Belirli bir hissenin son KAP bildirimlerini getir."""
        entries = self.fetch_notifications(
            max_entries=200,
            ticker_filter=ticker,
        )
        return [e.to_dict() for e in entries[:limit]]


async def fetch_kap_async(
    ticker_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Async ortamda KAP bildirimi çek."""
    watcher = KapWatcher()
    entries = await asyncio.to_thread(
        watcher.fetch_notifications,
        50,
        ticker_filter,
    )
    return [e.to_dict() for e in entries]


# Singleton
kap_watcher = KapWatcher()
