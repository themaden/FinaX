"""
FinanX — Makroekonomi Ajanı
Genel piyasa koşulları, enflasyon, faiz kararları ve sektör etkisi analizi.
"""

from typing import Dict, Any, Optional
from loguru import logger

from backend.llm_factory import get_llm
from backend.tools.kap_watcher import kap_watcher


MACRO_SYSTEM_PROMPT = """Sen FinanX'ın Makroekonomi Uzmanısın.
Türkiye ve küresel ekonomik gelişmelerin BIST hisseleri üzerindeki etkisini analiz ediyorsun.

ANALİZ KAPSAMI:
1. TCMB Para Politikası: Faiz kararları ve etkileri
2. Enflasyon Dinamikleri: TÜFE, ÜFE ve şirket maliyetlerine etkisi
3. Döviz Kuru Etkisi: TL/USD, TL/EUR dalgalanmaları
4. Sektör Analizi: İlgili sektörün makro duyarlılığı
5. Küresel Risk Faktörleri: Fed kararları, emtia fiyatları

YANIT FORMATI:
🌍 MAKROEKONOMİK ÇERÇEVE
[Genel makro durum değerlendirmesi]

📌 SEKTÖRE ETKİSİ
[Şirketin sektörüne özel makro etkiler]

⚠️ RİSK FAKTÖRLERİ
[Makro riskler]

✅ FIRSATLAR
[Makro destekler ve fırsatlar]

Her zaman Türkçe yanıt ver ve güncel Türkiye ekonomisi bağlamında değerlendir."""


# Türkiye makro verilerinin anlık kaynağı olmadığı için statik bağlam kullanılır
# Gerçek uygulamada TCMB API veya bir ekonomi veri servisi entegre edilir
TURKEY_MACRO_CONTEXT = """
TÜRK EKONOMİSİ GENEL BAĞLAM:
- TCMB politika faizi: Yüksek faiz dönemi (son TCMB kararları izlenmelidir)
- Enflasyon: Yüksek enflasyon ortamı, şirket maliyetlerini etkiliyor
- TL döviz kuru: Dalgalı kur rejimi, ihracatçı şirketlere fayda, ithalatçılara maliyet
- BIST100: Yüksek enflasyon döneminde hisse senetleri enflasyona karşı koruyucu olabilir
- Sektörel döngüler: Bankacılık, enerji, ihracat odaklı şirketler farklı maruziyete sahip
"""

SECTOR_MACRO_SENSITIVITY = {
    "bankacılık": "Yüksek faiz → net faiz marjı artışı. Faiz düşüşünde baskı.",
    "havacılık": "Jet yakıtı maliyeti, döviz kuru, turizm talebi etkili.",
    "demir çelik": "Küresel çelik fiyatları, enerji maliyetleri, inşaat sektörü talebi.",
    "perakende": "Tüketici harcamaları, enflasyon, döviz kuru (ithal mal maliyetleri).",
    "enerji": "Ham petrol fiyatları, EPDK düzenlemeleri, yenilenebilir enerji yatırımları.",
    "teknoloji": "Döviz kuru (yabancı müşteriler), ar-ge maliyetleri, siber güvenlik talebi.",
    "inşaat-gayrimenkul": "Faiz oranları, TOKİ politikaları, kredi erişilebilirliği.",
    "gıda-içecek": "Tarımsal hammadde, enerji maliyetleri, ihracat fırsatları.",
}


class MacroEconomistAgent:
    """
    Makroekonomi analizi yapan uzman ajan.
    """

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def _get_sector_context(self, sector: Optional[str]) -> str:
        """Sektöre özel makro bağlamı getir."""
        if not sector:
            return "Sektör bilgisi mevcut değil."

        sector_lower = sector.lower()
        for key, sensitivity in SECTOR_MACRO_SENSITIVITY.items():
            if key in sector_lower:
                return f"Sektör: {sector}\nMakro Duyarlılık: {sensitivity}"

        return f"Sektör: {sector}"

    async def analyze(
        self,
        ticker: str,
        sector: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Makroekonomi analizi yap.

        Args:
            ticker: Hisse sembolü
            sector: Şirketin sektörü
            query: Opsiyonel özel soru

        Returns:
            Dict: Makro analiz sonucu
        """
        ticker = ticker.upper()
        logger.info(f"Makro analiz başlatıldı: {ticker} (sektör={sector})")

        # KAP'tan son haberler
        recent_kap = []
        try:
            recent_kap = kap_watcher.get_notifications_for_ticker(ticker, limit=3)
        except Exception as e:
            logger.warning(f"KAP verisi alınamadı: {e}")

        # Bağlam oluştur
        sector_context = self._get_sector_context(sector)

        kap_context = ""
        if recent_kap:
            kap_items = "\n".join(
                f"- {n['title']} ({n.get('published_at', 'tarih yok')})"
                for n in recent_kap[:3]
            )
            kap_context = f"\nSON KAP BİLDİRİMLERİ:\n{kap_items}"

        messages = [
            {"role": "system", "content": MACRO_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Hisse: {ticker}\n"
                    f"{sector_context}\n"
                    f"{TURKEY_MACRO_CONTEXT}"
                    f"{kap_context}\n\n"
                    f"{'Özel soru: ' + query if query else 'Genel makro analiz yap'}"
                ),
            },
        ]

        try:
            llm = self._get_llm()
            response = await llm.ainvoke(messages)
            analysis_text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Makro analiz LLM hatası: {e}")
            analysis_text = f"Makroekonomi analizi tamamlanamadı: {str(e)}"

        return {
            "ticker": ticker,
            "agent": "macro_economist",
            "analysis": analysis_text,
            "sector": sector,
            "recent_kap": recent_kap,
        }


# Singleton
macro_agent = MacroEconomistAgent()
