"use client";

import React, { useState, useEffect } from "react";
import { Bell, Trash2, ShieldAlert, CheckCircle2, AlertTriangle, Send, RefreshCw, Plus } from "lucide-react";

interface Alarm {
  id: number;
  ticker: string;
  alarm_type: string;
  threshold_value: number | null;
  percent_threshold: number | null;
  kap_keyword: string | null;
  is_active: boolean;
  notes: string | null;
}

export default function AlarmsPage() {
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [activeOnly, setActiveOnly] = useState(true);
  const [loading, setLoading] = useState(false);

  // Form Fields
  const [ticker, setTicker] = useState("THYAO");
  const [alarmType, setAlarmType] = useState("price_above");
  const [threshold, setThreshold] = useState<number | "">("");
  const [percentThresh, setPercentThresh] = useState<number | "">("");
  const [kapKeyword, setKapKeyword] = useState("");
  const [telegramChat, setTelegramChat] = useState("");
  const [notes, setNotes] = useState("");

  const [formSuccess, setFormSuccess] = useState("");
  const [formError, setFormError] = useState("");
  
  const [testChatId, setTestChatId] = useState("");
  const [testSuccess, setTestSuccess] = useState("");
  const [testError, setTestError] = useState("");

  const loadAlarms = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/alarms?active_only=${activeOnly}`, {
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        setAlarms(data.alarms || []);
      }
    } catch {
      // Hata durumunu yut
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlarms();
  }, [activeOnly]);

  const handleCreateAlarm = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormSuccess("");
    setFormError("");

    if (!ticker.trim()) {
      setFormError("Hisse sembolü zorunludur.");
      return;
    }

    const payload = {
      ticker: ticker.toUpperCase().trim(),
      alarm_type: alarmType,
      threshold_value: threshold !== "" ? Number(threshold) : null,
      percent_threshold: percentThresh !== "" ? Number(percentThresh) : null,
      kap_keyword: kapKeyword.trim() || null,
      telegram_chat_id: telegramChat.trim() || null,
      notes: notes.trim() || null,
    };

    try {
      const res = await fetch("http://localhost:8000/api/v1/alarms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setFormSuccess(`✅ ${ticker.toUpperCase()} alarmı başarıyla kuruldu!`);
        setThreshold("");
        setPercentThresh("");
        setKapKeyword("");
        setNotes("");
        loadAlarms();
      } else {
        const data = await res.json();
        setFormError(data.detail || "Alarm oluşturulurken bir hata oluştu.");
      }
    } catch {
      setFormError("API sunucusuna bağlanılamadı.");
    }
  };

  const handleDeleteAlarm = async (id: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/alarms/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setAlarms((prev) => prev.filter((a) => a.id !== id));
      }
    } catch {
      alert("Silme işlemi başarısız.");
    }
  };

  const handleTestTelegram = async () => {
    setTestSuccess("");
    setTestError("");
    try {
      const url = testChatId.trim()
        ? `http://localhost:8000/api/v1/alarms/test-telegram?chat_id=${encodeURIComponent(testChatId.trim())}`
        : "http://localhost:8000/api/v1/alarms/test-telegram";
        
      const res = await fetch(url, { method: "POST" });
      if (res.ok) {
        setTestSuccess("Test mesajı Telegram hesabınıza gönderildi!");
      } else {
        const data = await res.json();
        setTestError(data.detail || "Test başarısız.");
      }
    } catch {
      setTestError("API sunucusuna bağlanılamadı.");
    }
  };

  const alarmTypeLabels: Record<string, string> = {
    price_above: "📈 Fiyat Üzerine Çıktı",
    price_below: "📉 Fiyat Altına Düştü",
    percent_change: "📊 Yüzdesel Değişim",
    kap_keyword: "📢 KAP Anahtar Kelime",
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight text-slate-100 flex items-center gap-2">
          <Bell className="w-8 h-8 text-cyan-400" /> Alarm Yönetimi
        </h1>
        <p className="text-xs text-slate-500 mt-1">Fiyat eşikleri veya KAP haber anahtar kelimeleri için Telegram bildirim sistemleri kurun.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Alarm Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card rounded-2xl p-6 space-y-5">
            <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Plus className="w-4.5 h-4.5 text-cyan-400" /> Yeni Alarm Oluştur
            </h3>

            <form onSubmit={handleCreateAlarm} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 font-bold block mb-1.5">Hisse Kodu</label>
                  <input
                    type="text"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value)}
                    placeholder="Örn: THYAO"
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none uppercase"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-400 font-bold block mb-1.5">Alarm Türü</label>
                  <select
                    value={alarmType}
                    onChange={(e) => setAlarmType(e.target.value)}
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
                  >
                    <option value="price_above">📈 Fiyat Eşiğin Üzerinde (TL)</option>
                    <option value="price_below">📉 Fiyat Eşiğin Altında (TL)</option>
                    <option value="percent_change">📊 Yüzdesel Değişim (%)</option>
                    <option value="kap_keyword">📢 KAP Anahtar Kelimesi</option>
                  </select>
                </div>
              </div>

              {/* Conditional Inputs based on Alarm Type */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(alarmType === "price_above" || alarmType === "price_below") && (
                  <div>
                    <label className="text-xs text-slate-400 font-bold block mb-1.5">Fiyat Eşiği (TL)</label>
                    <input
                      type="number"
                      value={threshold}
                      onChange={(e) => setThreshold(e.target.value !== "" ? Number(e.target.value) : "")}
                      placeholder="Fiyat girin..."
                      className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
                    />
                  </div>
                )}

                {alarmType === "percent_change" && (
                  <div>
                    <label className="text-xs text-slate-400 font-bold block mb-1.5">Yüzde Eşiği (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={percentThresh}
                      onChange={(e) => setPercentThresh(e.target.value !== "" ? Number(e.target.value) : "")}
                      placeholder="Yüzde girin..."
                      className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
                    />
                  </div>
                )}

                {alarmType === "kap_keyword" && (
                  <div>
                    <label className="text-xs text-slate-400 font-bold block mb-1.5">Anahtar Kelime</label>
                    <input
                      type="text"
                      value={kapKeyword}
                      onChange={(e) => setKapKeyword(e.target.value)}
                      placeholder="temettü, ihale vb..."
                      className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
                    />
                  </div>
                )}

                <div className="md:col-span-2">
                  <label className="text-xs text-slate-400 font-bold block mb-1.5">Telegram Chat ID (Opsiyonel)</label>
                  <input
                    type="text"
                    value={telegramChat}
                    onChange={(e) => setTelegramChat(e.target.value)}
                    placeholder="Boş bırakılırsa varsayılan kanal kullanılır"
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-bold block mb-1.5">Alarm Notu</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Kendinize not ekleyin..."
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none h-20 resize-none"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 hover:brightness-110 active:scale-[0.99] font-black text-sm py-3.5 rounded-xl transition-all shadow-[0_4px_20px_rgba(0,242,254,0.15)]"
              >
                🔔 Alarm Oluştur
              </button>
            </form>

            {formSuccess && (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-xs text-emerald-400">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{formSuccess}</span>
              </div>
            )}

            {formError && (
              <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-xs text-rose-400">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}
          </div>

          {/* Alarms list */}
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider">📋 Mevcut Alarmlarım</h3>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="active_only"
                  checked={activeOnly}
                  onChange={(e) => setActiveOnly(e.target.checked)}
                  className="rounded border-slate-800 text-cyan-500 focus:ring-cyan-500 bg-slate-950"
                />
                <label htmlFor="active_only" className="text-xs text-slate-400 font-bold select-none cursor-pointer">Sadece Aktifler</label>
              </div>
            </div>

            {loading ? (
              <div className="h-40 flex items-center justify-center">
                <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
              </div>
            ) : alarms.length > 0 ? (
              <div className="space-y-3.5">
                {alarms.map((alarm) => (
                  <div
                    key={alarm.id}
                    className="p-4 rounded-xl border border-slate-900 bg-slate-950/20 hover:border-slate-800/80 transition-all flex items-center justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm text-slate-100">{alarm.ticker}</span>
                        <span className="text-[10px] bg-slate-900 text-cyan-400 px-2 py-0.5 rounded-md font-bold uppercase tracking-wider">
                          {alarmTypeLabels[alarm.alarm_type] || alarm.alarm_type}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-medium">
                        {alarm.threshold_value !== null && `Eşik: ${alarm.threshold_value} TL`}
                        {alarm.percent_threshold !== null && `Değişim Eşiği: %${alarm.percent_threshold}`}
                        {alarm.kap_keyword !== null && `Anahtar Kelime: "${alarm.kap_keyword}"`}
                      </div>
                      {alarm.notes && <div className="text-[10px] text-slate-500 italic">Not: {alarm.notes}</div>}
                    </div>

                    <div className="flex items-center gap-4">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${alarm.is_active ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-slate-900 text-slate-500"}`}>
                        {alarm.is_active ? "🟢 Aktif" : "Pasif"}
                      </span>
                      <button
                        onClick={() => handleDeleteAlarm(alarm.id)}
                        className="text-slate-600 hover:text-rose-400 p-2 rounded-lg hover:bg-rose-500/5 transition-all"
                      >
                        <Trash2 className="w-4.5 h-4.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-8 bg-slate-950/10 border border-slate-900 rounded-xl text-slate-500 text-xs">
                Kayıtlı alarm bulunmamaktadır.
              </div>
            )}
          </div>
        </div>

        {/* Telegram config testing info */}
        <div className="space-y-6">
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4.5 h-4.5 text-cyan-400" /> Telegram Kurulumu
            </h3>
            
            <div className="text-xs text-slate-400 space-y-3 leading-relaxed">
              <p>
                Alarmların Telegram hesabınıza iletilebilmesi için aşağıdaki adımları tamamlamış olmalısınız:
              </p>
              <ol className="list-decimal list-inside space-y-2 pl-1 font-semibold text-slate-300">
                <li>
                  Telegram bot babası <a href="https://t.me/botfather" target="_blank" className="text-cyan-400 underline">@BotFather</a>&apos;dan `/newbot` komutuyla bot oluşturun.
                </li>
                <li>
                  Oluşan token&apos;ı `.env` dosyasına yazın: `TELEGRAM_BOT_TOKEN=...`
                </li>
                <li>
                  Chat ID&apos;nizi öğrenmek için <a href="https://t.me/userinfobot" target="_blank" className="text-cyan-400 underline">@userinfobot</a> ile konuşun.
                </li>
                <li>
                  Chat ID değerini `.env` dosyasına ekleyin: `TELEGRAM_CHAT_ID=...`
                </li>
              </ol>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Send className="w-4.5 h-4.5 text-cyan-400" /> Bağlantı Test Et
            </h3>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-500 font-bold block mb-1.5">Test Chat ID (Opsiyonel)</label>
                <input
                  type="text"
                  value={testChatId}
                  onChange={(e) => setTestChatId(e.target.value)}
                  placeholder="Chat ID girin..."
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none"
                />
              </div>

              <button
                onClick={handleTestTelegram}
                className="w-full bg-slate-900 border border-slate-800 hover:border-cyan-400/20 hover:bg-slate-900/60 font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
              >
                📨 Test Mesajı Gönder
              </button>

              {testSuccess && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[10px] text-emerald-400 font-semibold leading-relaxed">
                  {testSuccess}
                </div>
              )}

              {testError && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-[10px] text-rose-400 font-semibold leading-relaxed">
                  {testError}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
