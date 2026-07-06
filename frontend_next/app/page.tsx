"use client";

import React, { useEffect, useState } from "react";
import { Search, Brain, Zap, Bell, CheckCircle2, TrendingUp, AlertTriangle } from "lucide-react";

interface RagStats {
  total_vectors?: number;
  total_chunks?: number;
  tickers?: string[];
}

interface QuickResponse {
  answer?: string;
  route_type?: string;
  ticker?: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<RagStats | null>(null);
  const [isApiOnline, setIsApiOnline] = useState<boolean | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QuickResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Canlı fiyatlar için hisse listesi
  const [stocks, setStocks] = useState<Record<string, { price: number; change: number }>>({
    THYAO: { price: 285.40, change: 1.25 },
    EREGL: { price: 52.30, change: -0.45 },
    AKBNK: { price: 58.90, change: 2.10 },
    GARAN: { price: 118.50, change: 0.75 },
    KCHOL: { price: 212.10, change: -1.15 },
    BIMAS: { price: 485.00, change: 1.85 },
    TUPRS: { price: 164.30, change: -0.20 },
    TCELL: { price: 94.75, change: 1.10 }
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const healthRes = await fetch("http://localhost:8000/health", { cache: "no-store" });
        if (healthRes.ok) {
          setIsApiOnline(true);
        } else {
          setIsApiOnline(false);
        }
      } catch {
        setIsApiOnline(false);
      }

      try {
        const statsRes = await fetch("http://localhost:8000/api/v1/documents/stats");
        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setStats(statsData);
        }
      } catch (err) {
        // Sessizce yut
      }
    };

    fetchDashboardData();
    
    // Canlı fiyat güncellemelerini çek (arka planda)
    const fetchLivePrices = async () => {
      const updated = { ...stocks };
      for (const ticker of Object.keys(stocks)) {
        try {
          const res = await fetch("http://localhost:8000/api/v1/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: `${ticker} fiyatı nedir`, session_id: "home_prices" }),
          });
          if (res.ok) {
            const data = await res.json();
            const quote = data.metadata?.quote_data;
            if (quote && !quote.error) {
              updated[ticker] = {
                price: quote.price || updated[ticker].price,
                change: quote.change_pct !== undefined ? quote.change_pct : updated[ticker].change
              };
            }
          }
        } catch {
          // Hata durumunda varsayılan/mock fiyatta kal
        }
      }
      setStocks(updated);
    };

    // Fiyatları 10 saniye sonra çek
    const priceTimeout = setTimeout(fetchLivePrices, 2000);
    return () => clearTimeout(priceTimeout);
  }, [isApiOnline]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setResponse(null);
    setErrorMessage("");

    try {
      const res = await fetch("http://localhost:8000/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: "dashboard_quick_query" }),
      });
      if (res.ok) {
        const data = await res.json();
        setResponse(data);
      } else {
        setErrorMessage(`Hata oluştu (API Kod: ${res.status})`);
      }
    } catch {
      setErrorMessage("API sunucusuna bağlanılamadı. Lütfen backend'i çalıştırın.");
    } finally {
      setLoading(false);
    }
  };

  const fillQuestion = (ticker: string) => {
    setQuestion(`${ticker} hakkında kapsamlı analiz ve son fiyatını getir.`);
  };

  const routeLabels: Record<string, string> = {
    live_price: "📡 Canlı Borsa Verisi",
    rag: "📚 Faaliyet Raporu & RAG",
    technical: "📈 Teknik İndikatör Analizi",
    multi_agent: "🤖 Çoklu Ajan Konsensüsü",
    kap: "📢 KAP Bildirim Analizi",
    compare: "⚖️ Şirket Karşılaştırması",
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-10">
      {/* Welcome Header */}
      <div className="text-center space-y-2 mt-4">
        <h1 className="text-6xl font-black bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent tracking-tight select-none">
          FinanX
        </h1>
        <p className="text-slate-400 text-lg font-medium">BIST Yapay Zeka Destekli Finansal Analiz Platformu</p>
        <div className="flex justify-center gap-3 text-xs font-semibold text-cyan-400/90 uppercase tracking-wider">
          <span>RAG</span> • <span>Multi-Agent AI</span> • <span>Canlı Borsa</span> • <span>Telegram Alarmları</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <div className="p-3 bg-cyan-500/10 rounded-xl mb-4 text-cyan-400">
            <Brain className="w-6 h-6" />
          </div>
          <div className="text-xs text-slate-500 font-semibold tracking-wider uppercase">Semantik Bilgi</div>
          <div className="text-2xl font-extrabold text-cyan-300 mt-1">
            {stats?.total_vectors ? `${stats.total_vectors} Parça` : "0 Parça"}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">RAG Bilgi Bankası</div>
        </div>

        <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <div className="p-3 bg-indigo-500/10 rounded-xl mb-4 text-indigo-400">
            <Zap className="w-6 h-6" />
          </div>
          <div className="text-xs text-slate-500 font-semibold tracking-wider uppercase">Yapay Zeka</div>
          <div className="text-2xl font-extrabold text-indigo-300 mt-1">GEMINI 1.5</div>
          <div className="text-[10px] text-slate-400 mt-1">Doğal Dil Analiz Motoru</div>
        </div>

        <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <div className="p-3 bg-emerald-500/10 rounded-xl mb-4 text-emerald-400">
            <Bell className="w-6 h-6" />
          </div>
          <div className="text-xs text-slate-500 font-semibold tracking-wider uppercase">Zamanlayıcı</div>
          <div className="text-2xl font-extrabold text-emerald-300 mt-1">AKTİF</div>
          <div className="text-[10px] text-slate-400 mt-1">Canlı KAP & Fiyat Dinleyici</div>
        </div>

        <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <div className="p-3 bg-blue-500/10 rounded-xl mb-4 text-blue-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div className="text-xs text-slate-500 font-semibold tracking-wider uppercase">Sistem Durumu</div>
          <div className={`text-2xl font-extrabold mt-1 ${isApiOnline ? "text-emerald-400" : "text-rose-500"}`}>
            {isApiOnline ? "STABİL" : "OFFLINE"}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">API Servis Bağlantısı</div>
        </div>
      </div>

      {/* Feature Navigation Cards */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-300 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-cyan-400" /> Platform Özellikleri
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { icon: "💬", title: "AI Sohbet", desc: "KAP bilançolarında ve faaliyet raporlarında doğal dil aramaları yapın." },
            { icon: "🤖", title: "Çoklu Ajan", desc: "4 farklı uzmanın (Temel, Teknik, Makro, Raporlama) ortak borsa raporu." },
            { icon: "📡", title: "Canlı Veri", desc: "BIST canlı borsa verileri, RSI, MACD ve hareketli ortalama indikatörleri." },
            { icon: "🔔", title: "Akıllı Alarm", desc: "Fiyat limitleri ve KAP kelime eşleşmeleri için otomatik Telegram bildirimleri." }
          ].map((item) => (
            <div key={item.title} className="glass-card rounded-2xl p-6 space-y-2 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="text-3xl">{item.icon}</div>
                <h3 className="font-bold text-slate-200 text-md">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Popular Stocks Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-300">📊 Popüler BIST Hisseleri</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-4">
          {Object.entries(stocks).map(([ticker, info]) => {
            const isPositive = info.change >= 0;
            return (
              <button
                key={ticker}
                onClick={() => fillQuestion(ticker)}
                className="glass-card rounded-2xl p-4 text-center cursor-pointer transition-all active:scale-95 flex flex-col items-center justify-center hover:border-cyan-400/40"
              >
                <span className="font-bold text-slate-400 text-xs tracking-wider">{ticker}</span>
                <span className="font-extrabold text-sm text-slate-200 mt-1">{info.price.toFixed(2)} TL</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full mt-2 ${
                    isPositive ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {isPositive ? "+" : ""}{info.change.toFixed(2)}%
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* AI Quick Query Form */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-300">🔍 AI Hızlı Finansal Sorgulama</h2>
        <div className="glass-card rounded-2xl p-6">
          <form onSubmit={handleAsk} className="flex gap-4">
            <div className="relative flex-1">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Sorunuzu girin (Örn: THYAO RSI değeri nedir? veya AKBNK son KAP haberlerini yorumla...)"
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-3.5 pl-11 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
              />
              <Search className="absolute left-4 top-4 w-4 h-4 text-slate-500" />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-gradient-to-r from-cyan-400 to-blue-500 hover:brightness-110 active:scale-95 text-slate-950 text-sm font-bold px-6 py-3.5 rounded-xl transition-all shadow-[0_4px_20px_rgba(34,211,238,0.2)] disabled:opacity-50"
            >
              {loading ? "Analiz ediliyor..." : "Sorgula"}
            </button>
          </form>

          {/* Response area */}
          {errorMessage && (
            <div className="mt-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-sm text-rose-400">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {response && (
            <div className="mt-6 p-6 border-l-4 border-cyan-400 bg-slate-900/10 rounded-r-xl space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-slate-500 uppercase tracking-wider">
                <span>{routeLabels[response.route_type || ""] || "🤖 AI Yanıtı"}</span>
                {response.ticker && <span className="bg-blue-600/10 text-cyan-400 px-2 py-0.5 rounded-md">{response.ticker}</span>}
              </div>
              <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-line">
                {response.answer}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer warning */}
      <footer className="text-center text-[10px] text-slate-600 space-y-1 py-8">
        <div>FinanX Terminal v1.2 • AI Finansal Gösterge Paneli</div>
        <div className="text-slate-700">Bu platform bilgi amaçlı sunulmuştur ve yatırım tavsiyesi niteliği taşımaz.</div>
      </footer>
    </div>
  );
}
