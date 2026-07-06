"""
FinanX — Veritabanı Modelleri
SQLAlchemy ORM modelleri: Alarmlar, Portföy, Sohbet Geçmişi
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, Enum as SAEnum
)
from datetime import datetime
import enum

from backend.database.db import Base


class AlarmType(str, enum.Enum):
    PRICE_ABOVE = "price_above"       # Fiyat eşiğin üzerine çıktı
    PRICE_BELOW = "price_below"       # Fiyat eşiğin altına düştü
    PERCENT_CHANGE = "percent_change"  # Yüzdesel değişim
    KAP_KEYWORD = "kap_keyword"       # KAP'ta anahtar kelime bildirimi


class SentimentType(str, enum.Enum):
    POSITIVE = "pozitif"
    NEGATIVE = "negatif"
    NEUTRAL = "nötr"


class Alarm(Base):
    """Kullanıcı alarmları tablosu."""
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="default_user")
    ticker = Column(String(20), nullable=False, index=True)
    alarm_type = Column(SAEnum(AlarmType), nullable=False)
    threshold_value = Column(Float, nullable=True)
    percent_threshold = Column(Float, nullable=True)
    kap_keyword = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    telegram_chat_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    triggered_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Alarm {self.ticker} {self.alarm_type} {self.threshold_value}>"


class PortfolioHolding(Base):
    """Portföy pozisyonları tablosu."""
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="default_user", index=True)
    ticker = Column(String(20), nullable=False)
    shares = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    sector = Column(String(100), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PortfolioHolding {self.ticker} x{self.shares}>"


class ChatMessage(Base):
    """Sohbet geçmişi tablosu."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    agent_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ChatMessage {self.role} session={self.session_id}>"


class KapNotification(Base):
    """KAP bildirimleri cache tablosu."""
    __tablename__ = "kap_notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True, unique=True)
    published_at = Column(DateTime, nullable=True)
    sentiment = Column(SAEnum(SentimentType), nullable=True)
    sentiment_summary = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_processed = Column(Boolean, default=False)

    def __repr__(self):
        return f"<KapNotification {self.ticker} {self.title[:50]}>"


class DocumentIndex(Base):
    """Yüklenen PDF belgelerinin kayıt tablosu."""
    __tablename__ = "document_index"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(500), nullable=False)
    ticker = Column(String(20), nullable=True, index=True)
    doc_type = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    quarter = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    file_hash = Column(String(64), nullable=True, unique=True)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DocumentIndex {self.filename} indexed={self.is_indexed}>"
