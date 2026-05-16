"use client";

import { Gauge } from "lucide-react";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";

interface FearGreedItem {
  value: number;
  classification: string;
  timestamp: number;
}

function getSentimentColor(value: number): string {
  if (value <= 20) return "text-red-600";
  if (value <= 40) return "text-orange-500";
  if (value <= 60) return "text-yellow-500";
  if (value <= 80) return "text-lime-500";
  return "text-emerald-600";
}

function getSentimentBg(value: number): string {
  if (value <= 20) return "bg-red-50";
  if (value <= 40) return "bg-orange-50";
  if (value <= 60) return "bg-yellow-50";
  if (value <= 80) return "bg-lime-50";
  return "bg-emerald-50";
}

function getSentimentBarColor(value: number): string {
  if (value <= 20) return "bg-red-500";
  if (value <= 40) return "bg-orange-500";
  if (value <= 60) return "bg-yellow-500";
  if (value <= 80) return "bg-lime-500";
  return "bg-emerald-500";
}

export function FearGreedCard({ data }: { data: FearGreedItem[] }) {
  const { t } = useLocale();
  const latest = data[0];

  if (!latest) {
    return (
      <div className="bg-white rounded-xl border border-border p-4">
        <div className="flex items-center gap-2 mb-3">
          <Gauge className="w-5 h-5 text-accent-blue" />
          <h3 className="font-semibold text-primary-text">{t.market.fearGreed}</h3>
        </div>
        <div className="text-sm text-secondary-text py-4 text-center">No data</div>
      </div>
    );
  }

  const history = data.slice(1, 7).reverse();

  return (
    <div className="bg-white rounded-xl border border-border p-4">
      <div className="flex items-center gap-2 mb-4">
        <Gauge className="w-5 h-5 text-accent-blue" />
        <h3 className="font-semibold text-primary-text">{t.market.fearGreed}</h3>
      </div>

      <div className="flex items-center gap-4 mb-4">
        <div
          className={cn(
            "w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold",
            getSentimentBg(latest.value)
          )}
        >
          <span className={getSentimentColor(latest.value)}>{latest.value}</span>
        </div>
        <div>
          <div className={cn("text-lg font-semibold", getSentimentColor(latest.value))}>
            {latest.classification}
          </div>
          <div className="text-xs text-secondary-text">
            Updated {new Date(latest.timestamp * 1000).toLocaleDateString()}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all", getSentimentBarColor(latest.value))}
            style={{ width: `${latest.value}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-secondary-text mt-1">
          <span>{t.market.extremeFear}</span>
          <span>{t.market.neutral}</span>
          <span>{t.market.extremeGreed}</span>
        </div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-xs font-medium text-secondary-text mb-1">{t.market.fearGreedHistory}</div>
          <div className="flex items-end gap-1 h-16">
            {history.map((item, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className={cn("w-full rounded-t-sm transition-all", getSentimentBarColor(item.value))}
                  style={{ height: `${Math.max(item.value * 0.6, 4)}px` }}
                />
                <div className="text-[10px] text-secondary-text">
                  {new Date(item.timestamp * 1000).toLocaleDateString(undefined, { weekday: "narrow" })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
