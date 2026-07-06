"use client";

import React, { useState, useEffect, useRef } from "react";
import { MessageSquare, Send, Trash2, HelpCircle, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  route_type?: string;
  sources?: any[];
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Oturum kimliğini başlat ve yerel saklamadan mesajları yükle
  useEffect(() => {
    const savedSession = localStorage.getItem("finanx_chat_session");
    const session = savedSession || Math.random().toString(36).substring(2, 10);
    setSessionId(session);
    if (!savedSession) {
      localStorage.setItem("finanx_chat_session", session);
    }

    const savedMessages = localStorage.getItem(`finanx_messages_${session}`);
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
  }, []);

  // Mesajlar değiştikçe otomatik kaydır ve kaydet
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    if (sessionId && messages.length > 0) {
      localStorage.setItem(`finanx_messages_${sessionId}`, JSON.stringify(messages));
    }
  }, [messages, sessionId]);

  const handleSend = async (questionText: string) => {
    if (!questionText.trim()) return;

    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMsg: Message = { role: "user", content: questionText, timestamp: time };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: questionText, session_id: sessionId }),
      });

      if (res.ok) {
        const data = await res.json();
        const aiMsg: Message = {
          role: "assistant",
          content: data.answer || "Yanıt alınamadı.",
          route_type: data.route_type,
          sources: data.sources || [],
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, aiMsg]);
      } else {
        const errMsg: Message = {
          role: "assistant",
          content: `❌ Hata oluştu (API Kod: ${res.status}). Sunucu hatası.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, errMsg]);
      }
    } catch {
      const offlineMsg: Message = {
        role: "assistant",
        content: "❌ **API sunucusuna bağlanılamadı.** Lütfen backend sunucunuzun çalıştığından emin olun.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, offlineMsg]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    if (sessionId) {
      localStorage.removeItem(`finanx_messages_${sessionId}`);
    }
  };

  const routeLabels: Record<string, string> = {
    live_price: "📡 Canlı Veri",
    rag: "📚 Belge Araması",
    technical: "📈 Teknik Analiz",
    multi_agent: "🤖 Çoklu Ajan",
    kap: "📢 KAP Bildirimleri",
    compare: "⚖️ Karşılaştırma",
  };

  const exampleQuestions = [
    "THYAO bugünkü fiyatı nedir?",
    "EREGL teknik analizi yap",
    "AKBNK hakkında kapsamlı yatırım raporu oluştur",
    "Son bilançoya göre THY net kârı nedir?",
    "Bugün yayınlanan KAP bildirimleri neler?"
  ];

  return (
    <div className="flex h-screen bg-[#090b16] overflow-hidden">
      {/* Chat Sidebar */}
      <div className="w-80 bg-slate-950/60 border-r border-slate-900 p-6 flex flex-col justify-between shrink-0">
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-cyan-400" /> AI Sohbet
            </h2>
            <p className="text-xs text-slate-500 mt-1">Hisseler ve bilançolar hakkında semantik sorgular.</p>
          </div>

          <div className="h-[1px] bg-slate-900" />

          {/* Example Questions */}
          <div className="space-y-2">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-cyan-500" /> Örnek Sorular
            </div>
            {exampleQuestions.map((q) => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                disabled={loading}
                className="w-full text-left bg-slate-900/40 hover:bg-slate-900 border border-slate-800/80 hover:border-cyan-500/20 text-slate-400 hover:text-slate-200 px-4 py-2.5 rounded-xl text-xs font-medium transition-all active:scale-[0.98] leading-relaxed disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Clear & Session */}
        <div className="space-y-4">
          <button
            onClick={clearChat}
            className="w-full bg-slate-900/80 hover:bg-rose-950/20 border border-slate-800 hover:border-rose-500/20 text-slate-400 hover:text-rose-400 font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            <Trash2 className="w-4 h-4" /> Sohbeti Temizle
          </button>
          <div className="text-[10px] text-slate-600 text-center font-semibold">
            Oturum ID: <span className="text-slate-500">{sessionId}</span>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col justify-between h-full relative">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto space-y-4">
              <div className="text-5xl">🤖</div>
              <h2 className="text-xl font-bold text-cyan-400">Merhaba! Ben FinanX AI</h2>
              <p className="text-sm text-slate-400 leading-relaxed">
                BIST şirketlerinin bilançoları, faaliyet raporları, teknik göstergeleri ve canlı fiyatları hakkında sorularınızı yanıtlayabilirim.
              </p>
              <p className="text-xs text-slate-500 font-medium">
                Başlamak için sol menüdeki örnek sorulardan birine tıklayabilir veya aşağıdaki kutuya kendi sorunuzu yazabilirsiniz.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`rounded-2xl p-5 space-y-3 ${
                    msg.role === "user"
                      ? "bg-gradient-to-br from-cyan-500/10 to-blue-500/20 border border-cyan-500/35 text-slate-200 max-w-[80%]"
                      : "glass-card text-slate-200 max-w-[90%]"
                  }`}
                >
                  {/* Header/Info */}
                  <div className="flex items-center gap-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    {msg.role === "user" ? (
                      <span>👤 Siz</span>
                    ) : (
                      <span className="bg-blue-600/10 text-cyan-400 px-2 py-0.5 rounded-full border border-cyan-400/15">
                        {routeLabels[msg.route_type || ""] || "🤖 AI Yanıtı"}
                      </span>
                    )}
                    <span>•</span>
                    <span>{msg.timestamp}</span>
                  </div>

                  {/* Message Content */}
                  <div className="text-sm leading-relaxed whitespace-pre-line text-slate-200">
                    {msg.content}
                  </div>

                  {/* RAG Sources */}
                  {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {msg.sources.slice(0, 3).map((source: any, sIdx: number) => (
                        <div
                          key={sIdx}
                          title={source.filename}
                          className="bg-slate-950/80 border border-slate-800 hover:border-cyan-400/20 text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-all cursor-default"
                        >
                          📄 {source.filename?.substring(0, 20)}...
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          
          {/* Thinking indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="glass-card rounded-2xl px-6 py-4 flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                <span className="text-xs text-slate-400 font-semibold tracking-wide">Düşünülüyor...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-6 bg-slate-950/30 border-t border-slate-900/60">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(input);
            }}
            className="flex gap-4 max-w-4xl mx-auto"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              placeholder="BIST hakkında bir soru yazın... (Örn: EREGL temettü analizi)"
              className="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-5 py-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 hover:brightness-110 active:scale-95 px-6 py-4 rounded-xl font-extrabold text-sm flex items-center gap-2 transition-all shadow-[0_4px_20px_rgba(34,211,238,0.2)] disabled:opacity-50"
            >
              <Send className="w-4 h-4" /> Gönder
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
