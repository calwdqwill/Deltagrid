"use client";

import { useLocale } from "@/hooks/useLocale";
import { formatPercent, signalColor } from "@/lib/utils";

interface SpreadSummaryProps {
  spreadPct: number;
  netProfitPct: number;
  signal: string;
}

export function SpreadSummary({ spreadPct, netProfitPct, signal }: SpreadSummaryProps) {
  const { t } = useLocale();

  return (
    <div className="bg-gray-50 rounded-lg border border-border p-5">
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-xs font-medium uppercase tracking-wider text-secondary-text mb-1">
            {t.detail.spread}
          </div>
          <div className={`text-2xl font-bold tabular-nums ${spreadPct >= 0 ? "text-positive" : "text-negative"}`}>
            {formatPercent(spreadPct)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs font-medium uppercase tracking-wider text-secondary-text mb-1">
            {t.detail.netProfit}
          </div>
          <div className={`text-2xl font-bold tabular-nums ${netProfitPct >= 0 ? "text-positive" : "text-negative"}`}>
            {formatPercent(netProfitPct)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs font-medium uppercase tracking-wider text-secondary-text mb-1">
            {t.detail.signal}
          </div>
          <span
            className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold ${signalColor(signal)}`}
          >
            {t.signals[signal as keyof typeof t.signals] || signal}
          </span>
        </div>
      </div>
    </div>
  );
}
