"""
FinanX — /alarms Endpoint
Alarm oluşturma, listeleme ve silme CRUD işlemleri.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from loguru import logger

from backend.alarms.alarm_db import alarm_repository
from backend.alarms.notifier import telegram_notifier
from backend.database.models import AlarmType

router = APIRouter()


class CreateAlarmRequest(BaseModel):
    ticker: str = Field(..., description="Hisse sembolü (örn: THYAO)")
    alarm_type: AlarmType
    threshold_value: Optional[float] = Field(None, description="Fiyat eşiği (TL)")
    percent_threshold: Optional[float] = Field(None, description="Yüzde eşiği")
    kap_keyword: Optional[str] = Field(None, description="KAP arama kelimesi")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")
    user_id: str = Field(default="default_user")
    notes: Optional[str] = None


@router.post("/alarms", status_code=201)
async def create_alarm(request: CreateAlarmRequest, background_tasks: BackgroundTasks):
    """Yeni bir fiyat veya KAP alarmı oluştur."""
    alarm = await alarm_repository.create(
        ticker=request.ticker,
        alarm_type=request.alarm_type,
        threshold_value=request.threshold_value,
        percent_threshold=request.percent_threshold,
        kap_keyword=request.kap_keyword,
        telegram_chat_id=request.telegram_chat_id,
        user_id=request.user_id,
        notes=request.notes,
    )

    # Onay bildirimi gönder (arka planda)
    if request.telegram_chat_id or True:
        background_tasks.add_task(
            _send_alarm_created_notification,
            ticker=request.ticker,
            alarm_type=request.alarm_type.value,
            threshold=request.threshold_value or request.percent_threshold,
        )

    return {
        "message": "Alarm başarıyla oluşturuldu",
        "alarm": alarm_repository.alarm_to_dict(alarm),
    }


@router.get("/alarms")
async def list_alarms(user_id: str = "default_user", active_only: bool = False):
    """Alarm listesini döndür."""
    if active_only:
        alarms = await alarm_repository.list_active(user_id=user_id)
    else:
        alarms = await alarm_repository.list_all(user_id=user_id)

    return {
        "total": len(alarms),
        "alarms": [alarm_repository.alarm_to_dict(a) for a in alarms],
    }


@router.delete("/alarms/{alarm_id}")
async def delete_alarm(alarm_id: int):
    """Alarmı sil."""
    success = await alarm_repository.delete(alarm_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alarm bulunamadı: ID={alarm_id}")
    return {"message": f"Alarm {alarm_id} silindi"}


@router.patch("/alarms/{alarm_id}/deactivate")
async def deactivate_alarm(alarm_id: int):
    """Alarmı pasif yap (silmeden)."""
    success = await alarm_repository.deactivate(alarm_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alarm bulunamadı: ID={alarm_id}")
    return {"message": f"Alarm {alarm_id} pasif yapıldı"}


@router.post("/alarms/test-telegram")
async def test_telegram(chat_id: Optional[str] = None):
    """Telegram bağlantısını test et."""
    success = await telegram_notifier.test_connection(chat_id)
    if success:
        return {"message": "Telegram bağlantısı başarılı ✅"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Telegram bağlantısı başarısız. Bot token ve chat ID'yi kontrol edin.",
        )


async def _send_alarm_created_notification(ticker: str, alarm_type: str, threshold):
    """Alarm oluşturulduğunda opsiyonel bildirim."""
    try:
        message = (
            f"⚙️ *FinanX Alarm Kuruldu*\n\n"
            f"📌 Hisse: `{ticker}`\n"
            f"🔔 Tür: {alarm_type}\n"
            f"🎯 Eşik: {threshold}\n\n"
            f"_Koşul sağlandığında bildirim alacaksınız._"
        )
        await telegram_notifier.send_message(message)
    except Exception as e:
        logger.warning(f"Alarm oluşturma bildirimi gönderilemedi: {e}")
