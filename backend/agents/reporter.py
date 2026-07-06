"""
FinanX — Raporlama Ajanı
Temel, teknik ve makro analistlerin çıktılarını birleştirip Türkçe rapor üretir.
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from backend.llm_factory import get_llm


REPORTER_SYSTEM_PROMPT = """Sen FinanX'ın Baş Analisti ve Raporlama Uzmanısın.
Üç uzman ajanın analizlerini alıp yatırımcılar için anlaşılır, yapılandırılmış bir özet rapor hazırlıyorsun.

RAPOR YAPISI:
1. 📋 YÖNETİCİ ÖZETİ (3-4 cümle, kritik bulgular)
2. 💰 TEMEL ANALİZ BULGULARI (finansal sağlık)
3. 📈 TEKNİK ANALİZ BULGULARI (grafik sinyalleri)
4. 🌍 MAKROEKONOMİK BAĞLAM (ekonomik riskler ve fırsatlar)
5. ⚖️ GENEL DEĞERLENDİRME
6. 🎯 SONUÇ VE TAVSİYE (AL/TUT/SAT değil, sadece risk/fırsat değerlendirmesi)

ÖNEMLI NOTLAR:
- Yatırım tavsiyesi verme, yalnızca bilgi sun
- Belirsizlikleri açıkça belirt
- Tüm yanıtı Türkçe ver
- Markdown formatı kullan"""


class ReporterAgent:
    """
    Multi-agent çıktılarını birleştiren raporlama ajanı.
    """

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    async def create_report(
        self,
        ticker: str,
        fundamental_result: Optional[Dict[str, Any]] = None,
        technical_result: Optional[Dict[str, Any]] = None,
        macro_result: Optional[Dict[str, Any]] = None,
        original_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tüm ajan analizlerini birleştirerek kapsamlı rapor oluştur.

        Args:
            ticker: Hisse sembolü
            fundamental_result: Temel analiz ajanı çıktısı
            technical_result: Teknik analiz ajanı çıktısı
            macro_result: Makro analiz ajanı çıktısı
            original_query: Kullanıcının orijinal sorusu

        Returns:
            Dict: {
                "ticker": ...,
                "report": "Türkçe rapor metni",
                "executive_summary": "Kısa özet",
                "signal": "OLUMLU/OLUMSUZ/NÖTR"
            }
        """
        ticker = ticker.upper()
        logger.info(f"Raporlama başlatıldı: {ticker}")

        # Ajan çıktılarını birleştir
        context_sections = [f"# {ticker} ANALİZ RAPORU\n"]

        if fundamental_result and not fundamental_result.get("error"):
            context_sections.append(
                "## TEMEL ANALİZ\n" + fundamental_result.get("analysis", "Veri yok")
            )

        if technical_result and not technical_result.get("error"):
            signal = technical_result.get("overall_signal", "")
            context_sections.append(
                f"## TEKNİK ANALİZ (Genel Sinyal: {signal})\n"
                + technical_result.get("analysis", "Veri yok")
            )

        if macro_result and not macro_result.get("error"):
            context_sections.append(
                "## MAKROEKONOMİK ANALİZ\n" + macro_result.get("analysis", "Veri yok")
            )

        combined_context = "\n\n---\n\n".join(context_sections)

        if not combined_context.strip():
            return {
                "ticker": ticker,
                "agent": "reporter",
                "report": "Analiz için yeterli veri bulunamadı.",
                "executive_summary": "Veri yetersiz.",
                "signal": "NÖTR",
            }

        messages = [
            {"role": "system", "content": REPORTER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Aşağıdaki ajan analizlerini birleştirerek {ticker} için "
                    f"kapsamlı bir yatırımcı raporu hazırla:\n\n"
                    f"{combined_context}\n\n"
                    f"{'Kullanıcı sorusu: ' + original_query if original_query else ''}"
                ),
            },
        ]

        try:
            llm = self._get_llm()
            response = await llm.ainvoke(messages)
            report_text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Raporlama LLM hatası: {e}")
            report_text = f"Rapor oluşturulamadı: {str(e)}"

        # Teknik sinyalden genel sinyal belirle
        overall_signal = "NÖTR"
        if technical_result:
            sig = technical_result.get("overall_signal", "")
            if "YÜKSELEN" in sig or "YÜKSELEN" in sig:
                overall_signal = "OLUMLU"
            elif "DÜŞEN" in sig:
                overall_signal = "OLUMSUZ"

        return {
            "ticker": ticker,
            "agent": "reporter",
            "report": report_text,
            "signal": overall_signal,
            "component_results": {
                "fundamental": bool(fundamental_result and not fundamental_result.get("error")),
                "technical": bool(technical_result and not technical_result.get("error")),
                "macro": bool(macro_result and not macro_result.get("error")),
            },
        }


# Singleton
reporter_agent = ReporterAgent()
