"use client";

import { X } from "lucide-react";
import { useScannerStore } from "@/stores/scannerStore";
import { useUIStore } from "@/stores/uiStore";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";
import { VenueCard } from "./VenueCard";
import { SpreadSummary } from "./SpreadSummary";
import { CalculationBreakdown } from "./CalculationBreakdown";

export function DetailDrawer() {
  const { detailOpen, setDetailOpen } = useUIStore();
  const { data, selectedRecordId } = useScannerStore();
  const { t } = useLocale();

  const record = data?.records.find((r) => r.id === selectedRecordId);

  if (!detailOpen || !record) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={() => setDetailOpen(false)}
      />
      <div className="fixed right-0 top-0 h-full w-[480px] bg-white border-l border-border shadow-xl z-50 overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-border px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-primary-text">{t.detail.title}</h2>
          <button
            onClick={() => setDetailOpen(false)}
            className="p-2 rounded-lg hover:bg-row-hover text-secondary-text transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex items-center gap-3">
            {record.iconUrl && (
              <img src={record.iconUrl} alt={record.symbol} className="w-12 h-12 rounded-full" />
            )}
            <div>
              <div className="text-xl font-bold text-primary-text">{record.tokenName}</div>
              <div className="text-sm text-secondary-text">{record.pair}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <VenueCard
              type="buy"
              venue={record.buyVenue}
              price={record.buyPrice}
            />
            <VenueCard
              type="sell"
              venue={record.sellVenue}
              price={record.sellPrice}
            />
          </div>

          <SpreadSummary
            spreadPct={record.spreadPct}
            netProfitPct={record.netProfitPct}
            signal={record.signal}
          />

          <CalculationBreakdown
            buyPrice={record.buyPrice}
            sellPrice={record.sellPrice}
            spreadPct={record.spreadPct}
            netProfitPct={record.netProfitPct}
          />

          {(record.basisPct !== undefined || record.fundingRate !== undefined || record.openInterest !== undefined) && (
            <div className="bg-gray-50 rounded-lg border border-border p-4 space-y-3">
              <h3 className="text-sm font-semibold text-primary-text uppercase tracking-wider">
                Perp Details
              </h3>
              {record.basisPct !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-secondary-text">{t.detail.basis}</span>
                  <span className={cn("font-medium tabular-nums", record.basisPct >= 0 ? "text-positive" : "text-negative")}>
                    {record.basisPct.toFixed(4)}%
                  </span>
                </div>
              )}
              {record.fundingRate !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-secondary-text">{t.detail.fundingRate}</span>
                  <span className="font-medium tabular-nums text-primary-text">
                    {record.fundingRate.toFixed(6)}%
                  </span>
                </div>
              )}
              {record.openInterest !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-secondary-text">{t.detail.openInterest}</span>
                  <span className="font-medium tabular-nums text-primary-text">
                    ${record.openInterest.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          )}

          <div className="text-xs text-secondary-text">
            <div className="flex justify-between py-1">
              <span>Data status</span>
              <span className="font-medium">{record.dataStatus}</span>
            </div>
            <div className="flex justify-between py-1">
              <span>Source</span>
              <span className="font-medium">{record.sourceLabel}</span>
            </div>
            <div className="flex justify-between py-1">
              <span>Updated</span>
              <span className="font-medium">{new Date(record.updatedAt).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
