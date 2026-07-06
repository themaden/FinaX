"""
FinanX — /query Endpoint
Kullanıcı sorgularını RAG, Canlı Veri veya Multi-Agent yönlendirmesiyle işler.
"""

from typing import Optional, List
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from backend.agents.router import llm_router, RouteType
from backend.rag.retriever import rag_retriever
from backend.tools.live_price import get_quote_async, get_historical_async
from backend.tools.indicators import technical_indicators
from backend.agents.orchestrator import orchestrator
from backend.tools.kap_watcher import fetch_kap_async
from backend.tools.sentiment import sentiment_analyzer
from backend.database.models import ChatMessage
from backend.database.db import AsyncSessionLocal

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Kullanıcının Türkçe sorusu")
    session_id: str = Field(default="default", description="Sohbet oturumu ID'si")
    ticker_hint: Optional[str] = Field(None, description="Opsiyonel hisse sembolü ipucu")


class QueryResponse(BaseModel):
    answer: str
    route_type: str
    ticker: Optional[str] = None
    sources: List[dict] = []
    indicators: Optional[dict] = None
    metadata: dict = {}


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Kullanıcı sorusunu analiz edip en uygun modüle yönlendir.

    - Geçmişe yönelik sorular → RAG modülü
    - Anlık fiyat soruları → Live Price
    - Teknik analiz soruları → Technical Agent
    - Kapsamlı analiz → Multi-Agent Orchestrator
    - KAP soruları → KAP Watcher + Sentiment
    """
    question = request.question
    logger.info(f"Yeni sorgu: '{question[:60]}' (session={request.session_id})")

    # 1. LLM Router ile yönlendirme kararı al
    route = await llm_router.route(question)
    ticker = request.ticker_hint or route.ticker

    logger.info(f"Yönlendirme: {route.route} (ticker={ticker}, güven={route.confidence:.2f})")

    answer = ""
    sources: List[dict] = []
    indicators = None
    metadata: dict = {"route": route.route.value, "confidence": route.confidence}

    try:
        # ── RAG Modülü ──────────────────────────────────────────────────────
        if route.route == RouteType.RAG:
            result = await rag_retriever.query(
                question=question,
                ticker_filter=ticker,
            )
            answer = result["answer"]
            sources = result.get("sources", [])
            metadata["chunk_count"] = result.get("chunk_count", 0)

        # ── Canlı Fiyat ─────────────────────────────────────────────────────
        elif route.route == RouteType.LIVE_PRICE:
            if not ticker:
                answer = (
                    "Hangi hissenin fiyatını öğrenmek istiyorsunuz? "
                    "Lütfen hisse sembolünü (örn: THYAO, EREGL) belirtin."
                )
            else:
                quote = await get_quote_async(ticker)
                if quote.get("error"):
                    answer = f"❌ {ticker} için veri alınamadı: {quote['error']}"
                else:
                    change_emoji = "📈" if quote.get("change_pct", 0) >= 0 else "📉"
                    answer = (
                        f"## {ticker} Anlık Bilgiler {change_emoji}\n\n"
                        f"💰 **Fiyat:** `{quote.get('price', 'N/A')} TL`\n"
                        f"📊 **Günlük Değişim:** `{quote.get('change', 0):+.2f} TL "
                        f"(%{quote.get('change_pct', 0):+.2f})`\n"
                        f"📦 **Hacim:** `{quote.get('volume', 0):,}`\n"
                        f"📈 **F/K Oranı:** `{quote.get('pe_ratio', 'N/A')}`\n"
                        f"📉 **PD/DD:** `{quote.get('pb_ratio', 'N/A')}`\n"
                        f"🏛️ **Piyasa Değeri:** `{_format_market_cap(quote.get('market_cap'))}`\n"
                        f"📅 **52 Hafta:** `{quote.get('52w_low', 'N/A')} - {quote.get('52w_high', 'N/A')} TL`"
                    )
                    metadata["quote_data"] = quote

        # ── Teknik Analiz ────────────────────────────────────────────────────
        elif route.route == RouteType.TECHNICAL:
            if not ticker:
                answer = "Teknik analiz için lütfen hisse sembolünü belirtin."
            else:
                df = await get_historical_async(ticker, period="6mo")
                if df is not None and not df.empty:
                    tech_result = technical_indicators.analyze(df, ticker)
                    indicators = tech_result
                    answer = (
                        f"## {ticker} Teknik Analiz\n\n"
                        f"**Genel Sinyal:** {tech_result.get('overall_signal', 'N/A')}\n\n"
                        f"**RSI:** {tech_result.get('rsi', {}).get('value', 'N/A')} "
                        f"({tech_result.get('rsi', {}).get('signal', '')})\n\n"
                        "**Sinyaller:**\n" +
                        "\n".join(f"• {s}" for s in tech_result.get("signals", []))
                    )
                else:
                    answer = f"{ticker} için teknik veri bulunamadı."

        # ── Multi-Agent Analiz ────────────────────────────────────────────────
        elif route.route == RouteType.MULTI_AGENT:
            if not ticker:
                answer = "Kapsamlı analiz için lütfen hisse sembolünü belirtin."
            else:
                result = await orchestrator.run(ticker=ticker, query=question)
                answer = result.get("report", "Analiz tamamlanamadı.")
                indicators = result.get("indicators")
                metadata.update({
                    "signal": result.get("signal"),
                    "components": result.get("components_used"),
                })

        # ── KAP Bildirimleri ──────────────────────────────────────────────────
        elif route.route == RouteType.KAP:
            notifications = await fetch_kap_async(ticker_filter=ticker)
            if not notifications:
                answer = "Şu an KAP bildirimi bulunamadı."
            else:
                analyzed = await sentiment_analyzer.analyze_batch(notifications[:5])
                lines = [f"## KAP Bildirimleri{' — ' + ticker if ticker else ''}\n"]
                for notif, sent in zip(notifications[:5], analyzed):
                    emoji = sentiment_analyzer.get_sentiment_emoji(
                        sent.get("sentiment", "nötr")
                    )
                    lines.append(
                        f"{emoji} **{notif.get('title', 'Başlık yok')}**\n"
                        f"> {sent.get('summary', '')}\n"
                    )
                answer = "\n".join(lines)

        # ── Karşılaştırma ────────────────────────────────────────────────────
        elif route.route == RouteType.COMPARE:
            answer = (
                "Karşılaştırma için `/compare` endpoint'ini kullanın veya "
                "sorunuzu 'X ile Y hissesini karşılaştır' formatında tekrar yazın."
            )

        # ── Portföy ──────────────────────────────────────────────────────────
        elif route.route == RouteType.PORTFOLIO:
            answer = (
                "Portföy analizi için `/portfolio` endpoint'ini kullanın "
                "veya sol menüden Portföy sayfasını açın."
            )

        else:
            # Varsayılan: RAG
            result = await rag_retriever.query(question=question)
            answer = result["answer"]
            sources = result.get("sources", [])

    except Exception as e:
        logger.error(f"Sorgu işleme hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {str(e)}")

    # Sohbet geçmişine kaydet (arka planda, hatayı yutarak)
    await _save_chat_message(
        session_id=request.session_id,
        role="user",
        content=question,
    )
    await _save_chat_message(
        session_id=request.session_id,
        role="assistant",
        content=answer,
        sources=sources,
        agent_type=route.route.value,
    )

    return QueryResponse(
        answer=answer,
        route_type=route.route.value,
        ticker=ticker,
        sources=sources,
        indicators=indicators,
        metadata=metadata,
    )


async def _save_chat_message(
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[dict]] = None,
    agent_type: Optional[str] = None,
):
    """Sohbet mesajını veritabanına kaydet."""
    try:
        async with AsyncSessionLocal() as session:
            msg = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                sources=json.dumps(sources or [], ensure_ascii=False),
                agent_type=agent_type,
            )
            session.add(msg)
            await session.commit()
    except Exception as e:
        logger.warning(f"Sohbet kaydetme hatası: {e}")


def _format_market_cap(value) -> str:
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if v >= 1e12:
        return f"{v/1e12:.2f} Trilyon TL"
    elif v >= 1e9:
        return f"{v/1e9:.2f} Milyar TL"
    elif v >= 1e6:
        return f"{v/1e6:.2f} Milyon TL"
    return f"{v:,.2f} TL"
