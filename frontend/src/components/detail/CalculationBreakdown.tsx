"use client";

import { useLocale } from "@/hooks/useLocale";
import { formatPercent } from "@/lib/utils";

interface CalculationBreakdownProps {
  buyPrice: number;
  sellPrice: number;
  spreadPct: number;
  netProfitPct: number;
}

export function CalculationBreakdown({
  buyPrice,
  sellPrice,
  spreadPct,
  netProfitPct,
}: CalculationBreakdownProps) {
  const { t } = useLocale();
  const feeBuy = 0.1;
  const feeSell = 0.1;
  const slippage = 0.0;
  const totalCosts = feeBuy + feeSell + slippage;

  return (
    <div className="bg-white rounded-lg border border-border p-5">
      <h3 className="text-sm font-semibold text-primary-text uppercase tracking-wider mb-4">
        {t.detail.calculation}
      </h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between py-1">
          <span className="text-secondary-text">Gross Spread</span>
          <span className="font-medium text-primary-text tabular-nums">
            (({sellPrice.toFixed(2)} - {buyPrice.toFixed(2)}) / {buyPrice.toFixed(2)}) × 100
          </span>
        </div>
        <div className="flex justify-between py-1">
          <span className="text-secondary-text"></span>
          <span className="font-semibold text-positive tabular-nums">{formatPercent(spreadPct)}</span>
        </div>
        <div className="border-t border-border my-2" />
        <div className="flex justify-between py-1">
          <span className="text-secondary-text">Buy Fee ({feeBuy}%)</span>
          <span className="font-medium text-negative tabular-nums">-{feeBuy}%</span>
        </div>
        <div className="flex justify-between py-1">
          <span className="text-secondary-text">Sell Fee ({feeSell}%)</span>
          <span className="font-medium text-negative tabular-nums">-{feeSell}%</span>
        </div>
        <div className="flex justify-between py-1">
          <span className="text-secondary-text">Slippage ({slippage}%)</span>
          <span className="font-medium text-negative tabular-nums">-{slippage}%</span>
        </div>
        <div className="border-t border-border my-2" />
        <div className="flex justify-between py-1">
          <span className="text-secondary-text">Total Costs</span>
          <span className="font-medium text-negative tabular-nums">-{totalCosts}%</span>
        </div>
        <div className="flex justify-between py-2 bg-gray-50 rounded-md px-3 -mx-3">
          <span className="font-semibold text-primary-text">Net Profit</span>
          <span
            className={`font-bold tabular-nums ${netProfitPct >= 0 ? "text-positive" : "text-negative"}`}
          >
            {formatPercent(netProfitPct)}
          </span>
        </div>
      </div>
    </div>
  );
}
