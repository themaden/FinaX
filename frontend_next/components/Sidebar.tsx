"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, BarChart2, Briefcase, Bell, LayoutDashboard, Terminal } from "lucide-react";

interface HealthData {
  status?: string;
  version?: string;
  llm_provider?: string;
  alarm_scheduler?: boolean;
}

export default function Sidebar() {
  const pathname = usePathname();
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [healthData, setHealthData] = useState<HealthData | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch("http://localhost:8000/health", { cache: "no-store" });
        if (res.ok) {
          const data = await res.json();
          setIsHealthy(true);
          setHealthData(data);
        } else {
          setIsHealthy(false);
        }
      } catch (err) {
        setIsHealthy(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000); // 5 saniyede bir sağlık kontrolü
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "AI Sohbet", href: "/chat", icon: MessageSquare },
    { name: "Hisse Analizi", href: "/analysis", icon: BarChart2 },
    { name: "Portföy", href: "/portfolio", icon: Briefcase },
    { name: "Alarmlar", href: "/alarms", icon: Bell },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-900 flex flex-col justify-between h-screen sticky top-0 shrink-0">
      <div className="flex flex-col">
        {/* Logo */}
        <div className="p-6 text-center">
          <Link href="/" className="text-3xl font-black tracking-tight bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent hover:brightness-110 transition-all select-none">
            📈 FinanX
          </Link>
          <div className="text-[10px] text-slate-500 font-semibold tracking-widest mt-1 uppercase">BIST AI Terminal</div>
        </div>

        <div className="h-[1px] bg-gradient-to-r from-transparent via-slate-800 to-transparent mx-4 mb-6" />

        {/* Navigation */}
        <nav className="px-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
                  isActive
                    ? "bg-blue-600/10 text-cyan-400 border-l-2 border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.05)]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info & Connection Status */}
      <div className="p-4 flex flex-col gap-4">
        {/* Connection Status Card */}
        <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isHealthy === true
                  ? "bg-emerald-400 pulse-green"
                  : isHealthy === false
                  ? "bg-rose-500 pulse-red"
                  : "bg-amber-400"
              }`}
            />
            <span className="text-xs font-semibold text-slate-300">
              {isHealthy === true ? "API Bağlı" : isHealthy === false ? "Bağlantı Yok" : "Bağlanıyor..."}
            </span>
          </div>

          {isHealthy === true && healthData && (
            <div className="space-y-1">
              <div className="text-[10px] text-slate-500 font-medium">
                Yapay Zeka: <span className="text-indigo-400 font-semibold">{healthData.llm_provider?.toUpperCase()}</span>
              </div>
              <div className="text-[10px] text-slate-500 font-medium">
                Zamanlayıcı: <span className="text-emerald-400 font-semibold">{healthData.alarm_scheduler ? "Aktif" : "Pasif"}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Brand */}
        <div className="text-center">
          <div className="text-[10px] text-slate-600 font-medium">FinanX Terminal v1.2</div>
          <div className="text-[9px] text-slate-700 font-semibold mt-0.5">© {new Date().getFullYear()} Google DeepMind Team</div>
        </div>
      </div>
    </aside>
  );
}
