"""
FinanX — Telegram Bildirim Servisi
Alarm tetiklendiğinde Telegram üzerinden mesaj gönderir.
"""

import asyncio
from typing import Optional, Dict, Any
from loguru import logger

try:
    from telegram import Bot
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot kurulu değil")

from backend.config import settings


class TelegramNotifier:
    """
    Telegram Bot API ile bildirim gönderen servis.
    """

    def __init__(self):
        self._bot: Optional[Any] = None

    def _get_bot(self):
        """Lazy loading ile bot nesnesini oluştur."""
        if not TELEGRAM_AVAILABLE:
            raise RuntimeError("python-telegram-bot kurulu değil: pip install python-telegram-bot")

        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN ayarlanmamış. "
                ".env dosyasına ekleyin."
            )

        if self._bot is None:
            self._bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        return self._bot

    async def send_message(
        self,
        message: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
    ) -> bool:
        """
        Telegram'a mesaj gönder.

        Args:
            message: Gönderilecek mesaj metni (Markdown destekler)
            chat_id: Hedef chat ID (None ise config'den alır)
            parse_mode: "Markdown" veya "HTML"

        Returns:
            bool: Gönderim başarılı mı
        """
        target_chat_id = chat_id or settings.TELEGRAM_CHAT_ID

        if not target_chat_id:
            logger.warning("Telegram chat ID ayarlanmamış, bildirim gönderilemiyor")
            return False

        try:
            bot = self._get_bot()
            await bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN if parse_mode == "Markdown" else ParseMode.HTML,
            )
            logger.info(f"Telegram bildirimi gönderildi → chat_id: {target_chat_id[:10]}***")
            return True
        except Exception as e:
            logger.error(f"Telegram gönderim hatası: {e}")
            return False

    async def send_price_alert(
        self,
        ticker: str,
        current_price: float,
        threshold: float,
        direction: str,  # "yukarı" veya "aşağı"
        change_pct: Optional[float] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """Fiyat alarmı bildirimi gönder."""
        direction_emoji = "🟢📈" if direction == "yukarı" else "🔴📉"
        change_str = f" (%{change_pct:+.2f})" if change_pct is not None else ""

        message = (
            f"{direction_emoji} *FİNANX FİYAT ALARMI*\n\n"
            f"📌 *Hisse:* `{ticker}`\n"
            f"💰 *Anlık Fiyat:* `{current_price:.2f} TL`{change_str}\n"
            f"🎯 *Eşik Değer:* `{threshold:.2f} TL`\n"
            f"⚡ *Durum:* Fiyat eşiğin *{direction}* çıktı!\n\n"
            f"_FinanX - {self._get_timestamp()}_"
        )
        return await self.send_message(message, chat_id)

    async def send_kap_alert(
        self,
        ticker: str,
        title: str,
        url: str,
        sentiment: Optional[str] = None,
        summary: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """KAP bildirimi alarmı gönder."""
        sentiment_emoji = {
            "pozitif": "🟢",
            "negatif": "🔴",
            "nötr": "🟡",
        }.get(sentiment or "nötr", "⚪")

        message_parts = [
            f"📢 *KAP BİLDİRİMİ*\n",
            f"📌 *Hisse:* `{ticker}`",
            f"📰 *Başlık:* {title}",
        ]

        if sentiment:
            message_parts.append(f"{sentiment_emoji} *Duygu:* {sentiment.upper()}")

        if summary:
            message_parts.append(f"📝 *Özet:* {summary}")

        if url:
            message_parts.append(f"🔗 [KAP Bildirimine Git]({url})")

        message_parts.append(f"\n_FinanX - {self._get_timestamp()}_")

        message = "\n".join(message_parts)
        return await self.send_message(message, chat_id)

    async def send_percent_alert(
        self,
        ticker: str,
        current_price: float,
        change_pct: float,
        threshold_pct: float,
        chat_id: Optional[str] = None,
    ) -> bool:
        """Yüzdesel değişim alarmı gönder."""
        direction_emoji = "📈🟢" if change_pct > 0 else "📉🔴"

        message = (
            f"{direction_emoji} *FİNANX YÜZDELİK ALARM*\n\n"
            f"📌 *Hisse:* `{ticker}`\n"
            f"💰 *Anlık Fiyat:* `{current_price:.2f} TL`\n"
            f"📊 *Değişim:* `%{change_pct:+.2f}`\n"
            f"🎯 *Eşik:* `%{threshold_pct:.2f}`\n\n"
            f"_FinanX - {self._get_timestamp()}_"
        )
        return await self.send_message(message, chat_id)

    async def test_connection(self, chat_id: Optional[str] = None) -> bool:
        """Telegram bağlantısını test et."""
        message = (
            "🤖 *FinanX Telegram Bağlantısı Test Edildi* ✅\n\n"
            "Alarm sistemi başarıyla bağlandı.\n"
            f"_Zaman: {self._get_timestamp()}_"
        )
        return await self.send_message(message, chat_id)

    def _get_timestamp(self) -> str:
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%d.%m.%Y %H:%M")


# Singleton
telegram_notifier = TelegramNotifier()
