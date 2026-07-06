"use client";

import React, { useState, useEffect } from "react";
import { Search, Info, TrendingUp, TrendingDown, RefreshCw, BarChart2, BookOpen, MessageSquare, Bell } from "lucide-react";
import TradingViewChart from "@/components/TradingViewChart";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from "recharts";

interface QuoteData {
  price?: number;
  change?: number;
  change_pct?: number;
  volume?: number;
  pe_ratio?: number;
  pb_ratio?: number;
  sector?: string;
  error?: string;
}

interface IndicatorData {
  current_price?: number;
  overall_signal?: string;
  rsi?: { value: number; signal: string };
  bollinger?: { upper: number; middle: number; lower: number };
  signals?: string[];
  price_history?: {
    dates: string[];
    prices: number[];
    sma20: number[];
    sma50: number[];
    volume: number[];
  };
  error?: string;
}

export default function AnalysisPage() {
  const [ticker, setTicker] = useState("THYAO");
  const [searchInput, setSearchInput] = useState("THYAO");
  const [interval, setInterval] = useState("D");
  const [activeTab, setActiveTab] = useState("tradingview");
  
  const [quote, setQuote] = useState<QuoteData | null>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  
  const [techData, setTechData] = useState<IndicatorData | null>(null);
  const [techLoading, setTechLoading] = useState(false);

  const [agentReport, setAgentReport] = useState("");
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentSignal, setAgentSignal] = useState("");

  const [kapReport, setKapReport] = useState("");
  const [kapLoading, setKapLoading] = useState(false);

  const loadStockData = async (targetTicker: string) => {
    if (!targetTicker.trim()) return;
    
    setQuoteLoading(true);
    setQuote(null);
    setTechData(null);
    setAgentReport("");
    setAgentSignal("");
    setKapReport("");

    // 1. Fetch Quote
    try {
      const res = await fetch("http://localhost:8000/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: `${targetTicker} fiyatı`, session_id: "analysis_quote" }),
      });
      if (res.ok) {
        const data = await res.json();
        setQuote(data.metadata?.quote_data || {});
      }
    } catch (err) {
      console.error(err);
    } finally {
      setQuoteLoading(false);
    }

    // 2. Fetch Technical Indicators
    setTechLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: `${targetTicker} RSI MACD teknik analiz`, session_id: "analysis_tech" }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.indicators && !data.indicators.error) {
          setTechData(data.indicators);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setTechLoading(false);
    }
  };

  useEffect(() => {
    loadStockData(ticker);
  }, [ticker]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setTicker(searchInput.toUpperCase().trim());
    }
  };

  const handleRunAgentAnalysis = async () => {
    setAgentLoading(true);
    setAgentReport("");
    setAgentSignal("");
    try {
      const res = await fetch("http://localhost:8000/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: `${ticker} hakkında kapsamlı yatırım analizi yap`, session_id: "analysis_agent" }),
      });
      if (res.ok) {
        const data = await res.json();
        setAgentReport(data.answer || "Rapor alınamadı.");
        setAgentSignal(data.metadata?.signal || "NÖTR");
      }
    } catch (err) {
      setAgentReport("API sunucusuna bağlanılamadı.");
    } finally {
      setAgentLoading(false);
    }
  };

  const handleLoadKap = async () => {
    setKapLoading(true);
    setKapReport("");
    try {
      const res = await fetch("http://localhost:8000/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: `${ticker} son KAP bildirimleri nelerdir`, session_id: "analysis_kap" }),
      });
      if (res.ok) {
        const data = await res.json();
        setKapReport(data.answer || "KAP bildirimi bulunamadı.");
      }
    } catch (err) {
      setKapReport("API sunucusuna bağlanılamadı.");
    } finally {
      setKapLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "kap" && !kapReport) {
      handleLoadKap();
    }
  }, [activeTab]);

  // Recharts için veriyi dönüştür
  const getChartData = () => {
    if (!techData?.price_history) return [];
    const history = techData.price_history;
    return history.dates.map((date, idx) => ({
      name: date,
      fiyat: history.prices[idx] || 0,
      sma20: history.sma20[idx] || 0,
      sma50: history.sma50[idx] || 0,
      hacim: history.volume[idx] || 0
    }));
  };

  const chartData = getChartData();
  const latestPrice = quote?.price || techData?.current_price || 0;
  const priceChange = quote?.change || 0;
  const priceChangePct = quote?.change_pct || 0;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Top Search & Period Select */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-100 flex items-center gap-2">
            <BarChart2 className="w-8 h-8 text-cyan-400" /> {ticker} Analiz Paneli
          </h1>
          <p className="text-xs text-slate-500 mt-1">Canlı borsa grafikleri, teknik ve temel veriler.</p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <div className="relative">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Hisse kodu..."
                className="bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 pl-10 text-sm text-slate-100 focus:outline-none focus:border-cyan-400 w-44 uppercase"
              />
              <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
            </div>
            <button
              type="submit"
              className="bg-slate-900 border border-slate-800 hover:border-cyan-400/20 hover:bg-slate-900/60 font-bold text-xs px-5 py-2.5 rounded-xl transition-all"
            >
              Ara
            </button>
          </form>

          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
          >
            <option value="5">5 Dakika</option>
            <option value="15">15 Dakika</option>
            <option value="60">Saatlik</option>
            <option value="D">Günlük</option>
            <option value="W">Haftalık</option>
          </select>
        </div>
      </div>

      {/* Metrics Row */}
      {quoteLoading ? (
        <div className="h-20 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
        </div>
      ) : quote && !quote.error ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="glass-card rounded-xl p-5 text-center">
            <div className="text-xs text-slate-500 font-semibold tracking-wide uppercase">💰 Fiyat</div>
            <div className="text-xl font-black text-slate-100 mt-2">{latestPrice.toFixed(2)} TL</div>
            <div className={`text-xs font-bold mt-1 ${priceChange >= 0 ? "text-emerald-400" : "text-rose-500"}`}>
              {priceChange >= 0 ? "+" : ""}{priceChange.toFixed(2)} TL
            </div>
          </div>

          <div className="glass-card rounded-xl p-5 text-center">
            <div className="text-xs text-slate-500 font-semibold tracking-wide uppercase">📊 Değişim</div>
            <div className={`text-xl font-black mt-2 ${priceChangePct >= 0 ? "text-emerald-400" : "text-rose-500"}`}>
              {priceChangePct >= 0 ? "+" : ""}{priceChangePct.toFixed(2)}%
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Günlük Yüzde</div>
          </div>

          <div className="glass-card rounded-xl p-5 text-center">
            <div className="text-xs text-slate-500 font-semibold tracking-wide uppercase">📦 Hacim</div>
            <div className="text-xl font-black text-slate-100 mt-2">
              {quote.volume ? quote.volume.toLocaleString() : "N/A"}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Lot Adedi</div>
          </div>

          <div className="glass-card rounded-xl p-5 text-center">
            <div className="text-xs text-slate-500 font-semibold tracking-wide uppercase">📈 F/K Oranı</div>
            <div className="text-xl font-black text-indigo-300 mt-2">{quote.pe_ratio || "N/A"}</div>
            <div className="text-[10px] text-slate-500 mt-1">Fiyat / Kazanç</div>
          </div>

          <div className="glass-card rounded-xl p-5 text-center">
            <div className="text-xs text-slate-500 font-semibold tracking-wide uppercase">📉 PD/DD</div>
            <div className="text-xl font-black text-indigo-300 mt-2">{quote.pb_ratio || "N/A"}</div>
            <div className="text-[10px] text-slate-500 mt-1">Piyasa Değeri / Defter Değeri</div>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-slate-900/20 border border-slate-800 rounded-xl text-sm text-slate-400 text-center flex items-center justify-center gap-2">
          <Info className="w-4 h-4 text-cyan-400" /> {ticker} için canlı fiyat bilgisi alınamadı (Çevrimdışı Mod).
        </div>
      )}

      {/* Tabs list */}
      <div className="flex gap-2 border-b border-slate-900/80 pb-3">
        {[
          { id: "tradingview", label: "📈 Canlı Grafik", icon: BarChart2 },
          { id: "technical", label: "📊 Teknik İndikatörler", icon: TrendingUp },
          { id: "agent", label: "🤖 AI Ajan Raporu", icon: BookOpen },
          { id: "kap", label: "📢 KAP Bildirimleri", icon: Bell }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all ${
                isActive
                  ? "bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(0,242,254,0.08)]"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Contents */}
      <div className="space-y-6">
        {/* 1. TradingView Tab */}
        {activeTab === "tradingview" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-md text-slate-200">BIST {ticker} Canlı İnteraktif Grafik</h3>
            </div>
            <TradingViewChart ticker={ticker} interval={interval} height={550} />
          </div>
        )}

        {/* 2. Technical Tab */}
        {activeTab === "technical" && (
          <div className="space-y-6">
            <h3 className="font-bold text-md text-slate-200">İndikatör Analiz Göstergeleri</h3>
            
            {techLoading ? (
              <div className="h-60 flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              </div>
            ) : techData ? (
              <div className="space-y-6">
                {/* Metric breakdown cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="glass-card rounded-xl p-5 text-center">
                    <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">RSI (14) Değeri</div>
                    <div className="text-2xl font-black text-slate-200 mt-2">{techData.rsi?.value.toFixed(2) || "N/A"}</div>
                    <span className="inline-block bg-blue-600/10 text-cyan-400 border border-cyan-400/20 px-3 py-0.5 rounded-full text-[10px] font-bold mt-2 uppercase tracking-wide">
                      {techData.rsi?.signal || "NÖTR"}
                    </span>
                  </div>

                  <div className="glass-card rounded-xl p-5 text-center">
                    <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">Özet Teknik Yön</div>
                    <div className="text-2xl font-black text-cyan-400 mt-2">{techData.overall_signal}</div>
                    <div className="text-[10px] text-slate-500 mt-2">Hareketli Ortalamalar & Osilatörler</div>
                  </div>

                  <div className="glass-card rounded-xl p-5 text-center">
                    <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">Bollinger Bantları (20)</div>
                    {techData.bollinger ? (
                      <>
                        <div className="text-lg font-bold text-slate-200 mt-2">
                          Üst: {techData.bollinger.upper.toFixed(2)}
                        </div>
                        <div className="text-[10px] text-slate-500 mt-1">
                          Alt: {techData.bollinger.lower.toFixed(2)} • Orta: {techData.bollinger.middle.toFixed(2)}
                        </div>
                      </>
                    ) : (
                      <div className="text-2xl font-black text-slate-400 mt-2">N/A</div>
                    )}
                  </div>
                </div>

                {/* Recharts chart */}
                {chartData.length > 0 && (
                  <div className="glass-card rounded-2xl p-6 space-y-4">
                    <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wide">Fiyat ve Hareketli Ortalamalar (SMA)</h4>
                    <div className="w-full h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData}>
                          <XAxis dataKey="name" stroke="#475569" fontSize={10} />
                          <YAxis yAxisId="price" stroke="#475569" fontSize={10} domain={["auto", "auto"]} />
                          <YAxis yAxisId="volume" orientation="right" stroke="#475569" fontSize={10} hide />
                          <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#f8fafc" }} />
                          <Legend />
                          <Area yAxisId="price" type="monotone" dataKey="fiyat" fill="rgba(6, 182, 212, 0.05)" stroke="#06b6d4" strokeWidth={2} name="Kapanış" />
                          <Line yAxisId="price" type="monotone" dataKey="sma20" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="SMA 20" />
                          <Line yAxisId="price" type="monotone" dataKey="sma50" stroke="#10b981" strokeWidth={1.5} dot={false} name="SMA 50" />
                          <Bar yAxisId="volume" dataKey="hacim" fill="rgba(71, 85, 105, 0.15)" name="Hacim" />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Textual signals summary */}
                <div className="space-y-2">
                  <h4 className="font-bold text-xs text-slate-500 uppercase tracking-wider">İndikatör Sinyalleri</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {techData.signals?.map((sig, sIdx) => {
                      const isUp = sig.includes("📈") || sig.includes("📈") || sig.includes("Yükseliş");
                      return (
                        <div
                          key={sIdx}
                          className={`p-3.5 rounded-xl text-xs font-semibold flex items-center justify-between border ${
                            isUp
                              ? "bg-emerald-500/5 border-emerald-500/10 text-emerald-400"
                              : "bg-rose-500/5 border-rose-500/10 text-rose-400"
                          }`}
                        >
                          <span>{sig}</span>
                          <span>{isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center p-8 text-slate-500 text-sm">
                Teknik indikatör verisi yüklenemedi.
              </div>
            )}
          </div>
        )}

        {/* 3. AI Agent Tab */}
        {activeTab === "agent" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-md text-slate-200">🤖 Çoklu Ajan Konsensüs Raporu</h3>
                <p className="text-xs text-slate-500 mt-1">Temel, Teknik ve Makro analistlerinin ortak raporudur.</p>
              </div>

              {!agentReport && !agentLoading && (
                <button
                  onClick={handleRunAgentAnalysis}
                  className="bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 text-xs font-black px-6 py-3 rounded-xl hover:brightness-110 active:scale-95 transition-all shadow-[0_4px_15px_rgba(0,242,254,0.2)]"
                >
                  🤖 Analizi Çalıştır
                </button>
              )}
            </div>

            {agentLoading && (
              <div className="glass-card rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
                <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
                <div className="text-sm font-bold text-slate-300">AI Ajan Konsensüsü Hazırlanıyor...</div>
                <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                  Bu süreçte 4 farklı uzman AI borsa ve makro verilerini analiz ederek ortak bir rapor hazırlar. Lütfen bekleyin (yaklaşık 30-45 saniye).
                </p>
              </div>
            )}

            {agentReport && (
              <div className="space-y-6 animate-fadeIn">
                {/* Agent consensus signal card */}
                {agentSignal && (
                  <div
                    className={`p-5 rounded-2xl border font-bold flex items-center justify-between text-sm ${
                      agentSignal === "OLUMLU" || agentSignal === "AL"
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                        : agentSignal === "OLUMSUZ" || agentSignal === "SAT"
                        ? "bg-rose-500/10 border-rose-500/20 text-rose-400"
                        : "bg-blue-500/10 border-blue-500/20 text-cyan-400"
                    }`}
                  >
                    <span>🤖 Çoklu Ajan Karar Sinyali:</span>
                    <span className="text-lg font-black tracking-widest">{agentSignal}</span>
                  </div>
                )}

                {/* Markdown text */}
                <div className="glass-card rounded-2xl p-6 text-sm text-slate-300 leading-relaxed whitespace-pre-line space-y-2">
                  {agentReport}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 4. KAP Tab */}
        {activeTab === "kap" && (
          <div className="space-y-6">
            <h3 className="font-bold text-md text-slate-200">📢 {ticker} KAP Bildirimleri & Duygu Analizi</h3>
            
            {kapLoading ? (
              <div className="h-60 flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              </div>
            ) : kapReport ? (
              <div className="glass-card rounded-2xl p-6 text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                {kapReport}
              </div>
            ) : (
              <div className="text-center p-8 text-slate-500 text-sm">
                Bildirim bulunamadı.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
