"""
FinanX — LangGraph Multi-Agent Orkestrasyonu
Temel, Teknik, Makro ve Raporlama ajanlarını yöneten iş akışı.
"""

import asyncio
from typing import Dict, Any, Optional, TypedDict, Annotated
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph kurulu değil, basit sıralı orkestrasyon kullanılacak")

from backend.agents.fundamental import fundamental_agent
from backend.agents.technical import technical_agent
from backend.agents.macro import macro_agent
from backend.agents.reporter import reporter_agent
from backend.tools.live_price import live_price_service


class AgentState(TypedDict):
    """LangGraph için durum nesnesi."""
    ticker: str
    query: str
    sector: Optional[str]
    fundamental_result: Optional[Dict[str, Any]]
    technical_result: Optional[Dict[str, Any]]
    macro_result: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    errors: list


class MultiAgentOrchestrator:
    """
    Çoklu ajan iş akışını yöneten orkestratör.
    LangGraph kullanılabilirse StateGraph, yoksa sıralı async çalışma.
    """

    def __init__(self):
        self._graph = None
        if LANGGRAPH_AVAILABLE:
            self._build_graph()

    def _build_graph(self):
        """LangGraph StateGraph ile ajan iş akışını oluştur."""
        workflow = StateGraph(AgentState)

        # Node'ları ekle
        workflow.add_node("fundamental_analysis", self._fundamental_node)
        workflow.add_node("technical_analysis", self._technical_node)
        workflow.add_node("macro_analysis", self._macro_node)
        workflow.add_node("report_generation", self._reporter_node)

        # Başlangıç noktası
        workflow.set_entry_point("fundamental_analysis")

        # Bağlantılar — temel analiz sonrası teknik ve makro paralel çalışır
        workflow.add_edge("fundamental_analysis", "technical_analysis")
        workflow.add_edge("technical_analysis", "macro_analysis")
        workflow.add_edge("macro_analysis", "report_generation")
        workflow.add_edge("report_generation", END)

        self._graph = workflow.compile()
        logger.info("LangGraph iş akışı oluşturuldu")

    async def _fundamental_node(self, state: AgentState) -> AgentState:
        """Temel analiz düğümü."""
        try:
            result = await fundamental_agent.analyze(
                ticker=state["ticker"],
                query=state.get("query"),
            )
            state["fundamental_result"] = result
        except Exception as e:
            logger.error(f"Temel analiz düğüm hatası: {e}")
            state["errors"].append(f"fundamental: {str(e)}")
        return state

    async def _technical_node(self, state: AgentState) -> AgentState:
        """Teknik analiz düğümü."""
        try:
            result = await technical_agent.analyze(ticker=state["ticker"])
            state["technical_result"] = result
        except Exception as e:
            logger.error(f"Teknik analiz düğüm hatası: {e}")
            state["errors"].append(f"technical: {str(e)}")
        return state

    async def _macro_node(self, state: AgentState) -> AgentState:
        """Makro analiz düğümü."""
        try:
            result = await macro_agent.analyze(
                ticker=state["ticker"],
                sector=state.get("sector"),
                query=state.get("query"),
            )
            state["macro_result"] = result
        except Exception as e:
            logger.error(f"Makro analiz düğüm hatası: {e}")
            state["errors"].append(f"macro: {str(e)}")
        return state

    async def _reporter_node(self, state: AgentState) -> AgentState:
        """Raporlama düğümü."""
        try:
            result = await reporter_agent.create_report(
                ticker=state["ticker"],
                fundamental_result=state.get("fundamental_result"),
                technical_result=state.get("technical_result"),
                macro_result=state.get("macro_result"),
                original_query=state.get("query"),
            )
            state["final_report"] = result
        except Exception as e:
            logger.error(f"Raporlama düğüm hatası: {e}")
            state["errors"].append(f"reporter: {str(e)}")
        return state

    async def run(
        self,
        ticker: str,
        query: str = "",
        parallel: bool = True,
    ) -> Dict[str, Any]:
        """
        Tüm ajan analizini çalıştır.

        Args:
            ticker: Hisse sembolü
            query: Kullanıcı sorusu
            parallel: Teknik ve makro analizleri paralel çalıştır

        Returns:
            Dict: Kapsamlı analiz raporu
        """
        ticker = ticker.upper()
        logger.info(f"Multi-agent analiz başlatıldı: {ticker}")

        # Sektör bilgisini önceden al
        sector = None
        try:
            quote = live_price_service.get_quote(ticker)
            sector = quote.get("sector")
        except Exception:
            pass

        if LANGGRAPH_AVAILABLE and self._graph:
            # LangGraph iş akışı
            initial_state: AgentState = {
                "ticker": ticker,
                "query": query,
                "sector": sector,
                "fundamental_result": None,
                "technical_result": None,
                "macro_result": None,
                "final_report": None,
                "errors": [],
            }
            try:
                final_state = await self._graph.ainvoke(initial_state)
                return self._build_response(ticker, final_state)
            except Exception as e:
                logger.error(f"LangGraph hatası, fallback kullanılıyor: {e}")

        # Fallback: Sıralı/paralel async çalışma
        return await self._run_sequential_or_parallel(ticker, query, sector, parallel)

    async def _run_sequential_or_parallel(
        self,
        ticker: str,
        query: str,
        sector: Optional[str],
        parallel: bool,
    ) -> Dict[str, Any]:
        """LangGraph olmadan ajan çalıştırma."""
        errors = []

        if parallel:
            # Temel analiz önce, teknik+makro paralel
            try:
                fundamental_result = await fundamental_agent.analyze(ticker, query)
            except Exception as e:
                fundamental_result = None
                errors.append(f"fundamental: {e}")

            try:
                technical_result, macro_result = await asyncio.gather(
                    technical_agent.analyze(ticker),
                    macro_agent.analyze(ticker, sector, query),
                    return_exceptions=True,
                )
                if isinstance(technical_result, Exception):
                    errors.append(f"technical: {technical_result}")
                    technical_result = None
                if isinstance(macro_result, Exception):
                    errors.append(f"macro: {macro_result}")
                    macro_result = None
            except Exception as e:
                technical_result = None
                macro_result = None
                errors.append(f"parallel: {e}")
        else:
            # Tamamen sıralı
            fundamental_result = await fundamental_agent.analyze(ticker, query)
            technical_result = await technical_agent.analyze(ticker)
            macro_result = await macro_agent.analyze(ticker, sector, query)

        # Rapor oluştur
        final_report = await reporter_agent.create_report(
            ticker=ticker,
            fundamental_result=fundamental_result,
            technical_result=technical_result,
            macro_result=macro_result,
            original_query=query,
        )

        state = {
            "ticker": ticker,
            "sector": sector,
            "fundamental_result": fundamental_result,
            "technical_result": technical_result,
            "macro_result": macro_result,
            "final_report": final_report,
            "errors": errors,
        }
        return self._build_response(ticker, state)

    def _build_response(self, ticker: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """State'den son yanıt oluştur."""
        final_report = state.get("final_report") or {}
        technical = state.get("technical_result") or {}

        return {
            "ticker": ticker,
            "type": "multi_agent",
            "report": final_report.get("report", "Rapor oluşturulamadı."),
            "signal": final_report.get("signal", "NÖTR"),
            "technical_signal": technical.get("overall_signal", "YATAY"),
            "indicators": technical.get("indicators"),
            "fundamental_data": (state.get("fundamental_result") or {}).get("quote_data"),
            "errors": state.get("errors", []),
            "components_used": final_report.get("component_results", {}),
        }


# Singleton
orchestrator = MultiAgentOrchestrator()
