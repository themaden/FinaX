"use client";

import React, { useEffect, useRef } from "react";

interface TradingViewChartProps {
  ticker: string;
  interval?: string;
  height?: number;
}

export default function TradingViewChart({ ticker, interval = "D", height = 500 }: TradingViewChartProps) {
  const container = useRef<HTMLDivElement>(null);
  const containerId = `tv-chart-${ticker.toLowerCase()}`;

  useEffect(() => {
    if (!container.current) return;
    container.current.innerHTML = "";

    // create widget container inner div
    const widgetDiv = document.createElement("div");
    widgetDiv.id = containerId;
    widgetDiv.style.height = "100%";
    widgetDiv.style.width = "100%";
    container.current.appendChild(widgetDiv);

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.type = "text/javascript";
    script.async = true;
    script.onload = () => {
      if (typeof (window as any).TradingView !== "undefined") {
        new (window as any).TradingView.widget({
          width: "100%",
          height: height,
          symbol: `BIST:${ticker.toUpperCase()}`,
          interval: interval,
          timezone: "Europe/Istanbul",
          theme: "dark",
          style: "1",
          locale: "tr",
          enable_publishing: false,
          allow_symbol_change: true,
          container_id: containerId,
          studies: ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"],
        });
      }
    };

    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, [ticker, interval, height, containerId]);

  return (
    <div className="w-full bg-[#0e1117] rounded-2xl overflow-hidden border border-slate-900">
      <div ref={container} style={{ height: `${height}px` }} />
    </div>
  );
}
