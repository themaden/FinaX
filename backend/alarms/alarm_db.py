"""
FinanX — Alarm Veritabanı Yönetimi
Kullanıcı alarmlarını SQLite'ta saklar ve yönetir.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models import Alarm, AlarmType
from backend.database.db import AsyncSessionLocal


class AlarmRepository:
    """
    Alarm CRUD işlemlerini yöneten repository sınıfı.
    """

    async def create(
        self,
        ticker: str,
        alarm_type: AlarmType,
        threshold_value: Optional[float] = None,
        percent_threshold: Optional[float] = None,
        kap_keyword: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        user_id: str = "default_user",
        notes: Optional[str] = None,
    ) -> Alarm:
        """Yeni alarm oluştur."""
        alarm = Alarm(
            user_id=user_id,
            ticker=ticker.upper(),
            alarm_type=alarm_type,
            threshold_value=threshold_value,
            percent_threshold=percent_threshold,
            kap_keyword=kap_keyword,
            telegram_chat_id=telegram_chat_id,
            is_active=True,
            notes=notes,
        )
        async with AsyncSessionLocal() as session:
            session.add(alarm)
            await session.commit()
            await session.refresh(alarm)
            logger.info(f"Alarm oluşturuldu: {alarm}")
            return alarm

    async def list_active(
        self,
        user_id: Optional[str] = None,
        ticker: Optional[str] = None,
    ) -> List[Alarm]:
        """Aktif alarmları listele."""
        async with AsyncSessionLocal() as session:
            query = select(Alarm).where(Alarm.is_active == True)
            if user_id:
                query = query.where(Alarm.user_id == user_id)
            if ticker:
                query = query.where(Alarm.ticker == ticker.upper())
            result = await session.execute(query)
            return result.scalars().all()

    async def list_all(self, user_id: Optional[str] = None) -> List[Alarm]:
        """Tüm alarmları listele."""
        async with AsyncSessionLocal() as session:
            query = select(Alarm).order_by(Alarm.created_at.desc())
            if user_id:
                query = query.where(Alarm.user_id == user_id)
            result = await session.execute(query)
            return result.scalars().all()

    async def deactivate(self, alarm_id: int) -> bool:
        """Alarmı pasif yap."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update(Alarm)
                .where(Alarm.id == alarm_id)
                .values(is_active=False)
            )
            await session.commit()
            return result.rowcount > 0

    async def delete(self, alarm_id: int) -> bool:
        """Alarmı tamamen sil."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete(Alarm).where(Alarm.id == alarm_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def mark_triggered(self, alarm_id: int) -> bool:
        """Alarmın tetiklendiğini kaydet."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update(Alarm)
                .where(Alarm.id == alarm_id)
                .values(
                    triggered_at=datetime.utcnow(),
                    is_active=False,  # Bir kez tetiklendikten sonra kapat
                )
            )
            await session.commit()
            return result.rowcount > 0

    def alarm_to_dict(self, alarm: Alarm) -> Dict[str, Any]:
        """Alarm nesnesini dict'e dönüştür."""
        return {
            "id": alarm.id,
            "ticker": alarm.ticker,
            "alarm_type": alarm.alarm_type.value,
            "threshold_value": alarm.threshold_value,
            "percent_threshold": alarm.percent_threshold,
            "kap_keyword": alarm.kap_keyword,
            "is_active": alarm.is_active,
            "created_at": alarm.created_at.isoformat() if alarm.created_at else None,
            "triggered_at": alarm.triggered_at.isoformat() if alarm.triggered_at else None,
            "notes": alarm.notes,
        }


# Singleton
alarm_repository = AlarmRepository()
