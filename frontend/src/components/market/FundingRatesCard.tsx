"use client";

import { Wallet } from "lucide-react";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";

interface FundingRateItem {
  symbol: string;
  rate: number;
  interval: string;
  exchange: string;
  annualized: number;
}

export function FundingRatesCard({ items }: { items: FundingRateItem[] }) {
  const { t } = useLocale();

  return (
    <div className="bg-white rounded-xl border border-border p-4">
      <div className="flex items-center gap-2 mb-3">
        <Wallet className="w-5 h-5 text-accent-blue" />
        <h3 className="font-semibold text-primary-text">{t.market.fundingRates}</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 font-medium">
          Mock
        </span>
      </div>
      <div className="space-y-1">
        {items.map((item) => (
          <div
            key={item.symbol}
            className="flex items-center justify-between p-2 rounded-lg hover:bg-row-hover transition-colors"
          >
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-[10px] font-bold text-secondary-text">
                {item.symbol.slice(0, 3)}
              </div>
              <div>
                <div className="text-sm font-medium text-primary-text">{item.symbol}/USD</div>
                <div className="text-[10px] text-secondary-text">{item.exchange}</div>
              </div>
            </div>
            <div className="text-right">
              <div
                className={cn(
                  "text-sm font-semibold",
                  item.rate > 0 ? "text-emerald-600" : "text-red-600"
                )}
              >
                {(item.rate * 100).toFixed(3)}%
              </div>
              <div className="text-[10px] text-secondary-text">{item.interval}</div>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="text-sm text-secondary-text py-4 text-center">No data</div>
        )}
      </div>
    </div>
  );
}
