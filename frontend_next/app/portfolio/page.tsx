"use client";

import React, { useState, useEffect } from "react";
import { Briefcase, AlertTriangle, Plus, Trash2, PieChart, Info, RefreshCw, TrendingUp } from "lucide-react";
import {
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend
} from "recharts";

interface Holding {
  ticker: string;
  shares: number;
  avg_cost: number;
}

interface PortfolioItem extends Holding {
  current_price: number;
  current_value: number;
  pnl: number;
  pnl_pct: number;
  weight_pct: number;
}

interface PortfolioResult {
  summary: {
    total_cost: number;
    total_current_value: number;
    total_pnl: number;
    total_pnl_pct: number;
    diversification_score: number;
    portfolio_beta?: number;
  };
  holdings: PortfolioItem[];
  betas: {
    individual_betas: Record<string, number | null>;
    portfolio_beta?: number;
  };
  risk_analysis?: string;
}

const COLORS = ["#00f2fe", "#4facfe", "#10b981", "#f59e0b", "#9b51e0", "#ff4b4b", "#06b6d4"];

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([
    { ticker: "THYAO", shares: 100, avg_cost: 250.0 },
    { ticker: "AKBNK", shares: 500, avg_cost: 45.0 },
    { ticker: "EREGL", shares: 200, avg_cost: 80.0 },
  ]);

  const [newTicker, setNewTicker] = useState("");
  const [newShares, setNewShares] = useState<number | "">("");
  const [newCost, setNewCost] = useState<number | "">("");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PortfolioResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const handleAddRow = () => {
    if (!newTicker.trim() || !newShares || !newCost) return;
    
    const exists = holdings.some((h) => h.ticker.toUpperCase() === newTicker.toUpperCase().trim());
    if (exists) {
      setErrorMessage("Bu hisse zaten portföyünüzde ekli.");
      return;
    }

    setHoldings((prev) => [
      ...prev,
      {
        ticker: newTicker.toUpperCase().trim(),
        shares: Number(newShares),
        avg_cost: Number(newCost),
      },
    ]);
    setNewTicker("");
    setNewShares("");
    setNewCost("");
    setErrorMessage("");
  };

  const handleRemoveRow = (index: number) => {
    setHoldings((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleAnalyze = async () => {
    if (holdings.length === 0) {
      setErrorMessage("Portföyü analiz etmek için en az bir hisse eklemelisiniz.");
      return;
    }

    setLoading(true);
    setResult(null);
    setErrorMessage("");

    try {
      const res = await fetch("http://localhost:8000/api/v1/portfolio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ holdings }),
      });
      
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        setErrorMessage(`API hatası: ${res.status}`);
      }
    } catch {
      setErrorMessage("API sunucusuna bağlanılamadı. Lütfen backend'i çalıştırın.");
    } finally {
      setLoading(false);
    }
  };

  // Pie chart verileri
  const pieData = result?.holdings.map((h) => ({
    name: h.ticker,
    value: h.weight_pct,
  })) || [];

  // Bar chart verileri
  const barData = result?.holdings.map((h) => ({
    name: h.ticker,
    PnL: h.pnl_pct,
  })) || [];

  const summary = result?.summary;
  const betas = result?.betas;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight text-slate-100 flex items-center gap-2">
          <Briefcase className="w-8 h-8 text-cyan-400" /> Portföy Risk Analizi
        </h1>
        <p className="text-xs text-slate-500 mt-1">Hisselerinizi girip borsa beta değerlerini ve AI risk raporunu oluşturun.</p>
      </div>

      {/* Inputs Form Section */}
      <div className="glass-card rounded-2xl p-6 space-y-6">
        <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider">📝 Portföy Girişi</h3>
        
        {/* Dynamic add line */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="text-xs text-slate-400 font-bold block mb-2">Hisse Kodu</label>
            <input
              type="text"
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              placeholder="Örn: THYAO"
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none uppercase"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 font-bold block mb-2">Lot Adedi</label>
            <input
              type="number"
              value={newShares}
              onChange={(e) => setNewShares(e.target.value !== "" ? Number(e.target.value) : "")}
              placeholder="Örn: 100"
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 font-bold block mb-2">Ortalama Maliyet (TL)</label>
            <input
              type="number"
              step="0.01"
              value={newCost}
              onChange={(e) => setNewCost(e.target.value !== "" ? Number(e.target.value) : "")}
              placeholder="Örn: 250"
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
            />
          </div>
          <button
            onClick={handleAddRow}
            className="bg-cyan-500/10 border border-cyan-500/30 hover:bg-cyan-500/20 text-cyan-400 font-bold text-xs py-3.5 px-6 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" /> Ekle
          </button>
        </div>

        {/* Existing items list */}
        {holdings.length > 0 ? (
          <div className="border border-slate-900 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/60 text-slate-500 uppercase font-bold border-b border-slate-900">
                  <th className="p-4">Hisse Kodu</th>
                  <th className="p-4">Lot Adedi</th>
                  <th className="p-4">Ort. Maliyet</th>
                  <th className="p-4 w-20 text-center">Sil</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-900/60 bg-slate-950/10">
                {holdings.map((h, index) => (
                  <tr key={index} className="hover:bg-slate-900/20 text-slate-200">
                    <td className="p-4 font-bold text-cyan-400">{h.ticker}</td>
                    <td className="p-4">{h.shares}</td>
                    <td className="p-4">{h.avg_cost.toFixed(2)} TL</td>
                    <td className="p-4 text-center">
                      <button
                        onClick={() => handleRemoveRow(index)}
                        className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/5 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center p-8 bg-slate-950/20 border border-slate-900 rounded-xl text-slate-500 text-xs">
            Portföy listesi boş. Analiz için yukarıdan hisse ekleyin.
          </div>
        )}

        <button
          onClick={handleAnalyze}
          disabled={loading || holdings.length === 0}
          className="w-full bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 hover:brightness-110 active:scale-[0.99] font-black text-sm py-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-[0_4px_25px_rgba(0,242,254,0.15)] disabled:opacity-50"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" /> Portföy Hesaplanıyor...
            </>
          ) : (
            "📊 Portföyü Analiz Et"
          )}
        </button>

        {errorMessage && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-xs text-rose-400">
            <AlertTriangle className="w-4 h-4" />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* Results Section */}
      {result && summary && (
        <div className="space-y-8 animate-fadeIn">
          {/* Summary metrics row */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="glass-card rounded-xl p-5 text-center">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">💰 Toplam Değer</div>
              <div className="text-xl font-black text-slate-100 mt-2">{summary.total_current_value.toLocaleString(undefined, { maximumFractionDigits: 0 })} TL</div>
              <div className="text-[10px] text-slate-500 mt-1">Anlık Portföy Değeri</div>
            </div>

            <div className="glass-card rounded-xl p-5 text-center">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">📈 Toplam K/Z</div>
              <div className={`text-xl font-black mt-2 ${summary.total_pnl >= 0 ? "text-emerald-400" : "text-rose-500"}`}>
                {summary.total_pnl >= 0 ? "+" : ""}{summary.total_pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })} TL
              </div>
              <div className={`text-[10px] font-bold mt-1 ${summary.total_pnl >= 0 ? "text-emerald-400" : "text-rose-500"}`}>
                {summary.total_pnl_pct >= 0 ? "+" : ""}{summary.total_pnl_pct.toFixed(2)}%
              </div>
            </div>

            <div className="glass-card rounded-xl p-5 text-center">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">🎲 Çeşitlendirme</div>
              <div className="text-xl font-black text-cyan-400 mt-2">%{summary.diversification_score.toFixed(1)}</div>
              <div className="text-[10px] text-slate-500 mt-1">Varlık Dağılım Kalitesi</div>
            </div>

            <div className="glass-card rounded-xl p-5 text-center">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">⚡ Portföy Beta</div>
              <div className="text-xl font-black text-indigo-300 mt-2">
                {summary.portfolio_beta ? summary.portfolio_beta.toFixed(2) : "N/A"}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">BIST 100 Duyarlılığı</div>
            </div>

            <div className="glass-card rounded-xl p-5 text-center">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider">⚖️ Risk Seviyesi</div>
              <div className="text-xl font-black mt-2">
                {summary.diversification_score > 70 ? (
                  <span className="text-emerald-400">🟢 Düşük</span>
                ) : summary.diversification_score > 40 ? (
                  <span className="text-amber-400">🟡 Orta</span>
                ) : (
                  <span className="text-rose-400">🔴 Yüksek</span>
                )}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">Risk Dağılım Katmanı</div>
            </div>
          </div>

          {/* Visual analysis section (Charts) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card rounded-2xl p-6 space-y-4">
              <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <PieChart className="w-4 h-4 text-cyan-400" /> Portföy Dağılım Ağırlıkları
              </h3>
              <div className="w-full h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip formatter={(val) => `%${Number(val).toFixed(1)}`} />
                    <RechartsLegend verticalAlign="bottom" height={36} />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-card rounded-2xl p-6 space-y-4">
              <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" /> Hisselerin K/Z Durumu (%)
              </h3>
              <div className="w-full h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData}>
                    <XAxis dataKey="name" stroke="#475569" fontSize={10} />
                    <YAxis stroke="#475569" fontSize={10} tickFormatter={(tick) => `%${tick}`} />
                    <RechartsTooltip formatter={(val) => `%${Number(val).toFixed(2)}`} />
                    <Bar dataKey="PnL" radius={[6, 6, 0, 0]}>
                      {barData.map((entry, index) => {
                        const isPositive = entry.PnL >= 0;
                        return <Cell key={`cell-${index}`} fill={isPositive ? "#10b981" : "#ef4444"} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Detailed holdings table */}
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider">📋 Detaylı Pozisyonlar</h3>
            <div className="border border-slate-900 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950/60 text-slate-500 uppercase font-bold border-b border-slate-900">
                    <th className="p-4">Hisse</th>
                    <th className="p-4">Adet</th>
                    <th className="p-4">Maliyet</th>
                    <th className="p-4">Fiyat</th>
                    <th className="p-4">Değer</th>
                    <th className="p-4">K/Z</th>
                    <th className="p-4">K/Z %</th>
                    <th className="p-4">Ağırlık</th>
                    <th className="p-4">Beta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900/60 bg-slate-950/10 text-slate-200">
                  {result.holdings.map((h, idx) => {
                    const isPositive = h.pnl >= 0;
                    return (
                      <tr key={idx} className="hover:bg-slate-900/10">
                        <td className="p-4 font-bold text-cyan-400">{h.ticker}</td>
                        <td className="p-4">{h.shares}</td>
                        <td className="p-4">{h.avg_cost.toFixed(2)} TL</td>
                        <td className="p-4">{h.current_price.toFixed(2)} TL</td>
                        <td className="p-4">{h.current_value.toLocaleString(undefined, { maximumFractionDigits: 0 })} TL</td>
                        <td className={`p-4 font-semibold ${isPositive ? "text-emerald-400" : "text-rose-500"}`}>
                          {isPositive ? "+" : ""}{h.pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })} TL
                        </td>
                        <td className={`p-4 font-semibold ${isPositive ? "text-emerald-400" : "text-rose-500"}`}>
                          {isPositive ? "+" : ""}{h.pnl_pct.toFixed(2)}%
                        </td>
                        <td className="p-4">%{h.weight_pct.toFixed(1)}</td>
                        <td className="p-4 text-indigo-300 font-bold">
                          {betas?.individual_betas[h.ticker] ? Number(betas.individual_betas[h.ticker]).toFixed(2) : "N/A"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* AI Risk assessment report */}
          {result.risk_analysis && (
            <div className="space-y-4">
              <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Info className="w-4.5 h-4.5 text-cyan-400" /> 🤖 AI Risk Değerlendirmesi
              </h3>
              <div className="glass-card rounded-2xl p-6 text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                {result.risk_analysis}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
