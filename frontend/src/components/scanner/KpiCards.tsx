"use client";

import { TrendingUp, BarChart3, Zap, Target } from "lucide-react";
import { useScannerStore } from "@/stores/scannerStore";
import { useLocale } from "@/hooks/useLocale";
import { formatPercent, formatVolume } from "@/lib/utils";

export function KpiCards() {
  const { filteredRecords } = useScannerStore();
  const { t } = useLocale();

  const opportunities = filteredRecords.length;
  const bestSpread = filteredRecords.length > 0
    ? Math.max(...filteredRecords.map((r) => r.spreadPct))
    : 0;
  const avgSpread = filteredRecords.length > 0
    ? filteredRecords.reduce((sum, r) => sum + r.spreadPct, 0) / filteredRecords.length
    : 0;
  const activeSignals = filteredRecords.filter(
    (r) => r.signal === "STRONG" || r.signal === "BUY_SELL"
  ).length;

  const cards = [
    {
      label: t.kpi.opportunities,
      value: opportunities.toString(),
      icon: BarChart3,
      color: "text-accent-blue",
      bg: "bg-blue-50",
    },
    {
      label: t.kpi.bestSpread,
      value: formatPercent(bestSpread),
      icon: TrendingUp,
      color: "text-positive",
      bg: "bg-emerald-50",
    },
    {
      label: t.kpi.avgSpread,
      value: formatPercent(avgSpread),
      icon: Target,
      color: "text-secondary-text",
      bg: "bg-gray-50",
    },
    {
      label: t.kpi.activeSignals,
      value: activeSignals.toString(),
      icon: Zap,
      color: "text-marginal-signal",
      bg: "bg-amber-50",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-lg border border-border p-4 shadow-card"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-secondary-text">
              {card.label}
            </span>
            <div className={`p-1.5 rounded-md ${card.bg}`}>
              <card.icon className={`w-4 h-4 ${card.color}`} />
            </div>
          </div>
          <div className="text-2xl font-semibold text-primary-text tabular-nums">
            {card.value}
          </div>
        </div>
      ))}
    </div>
  );
}
