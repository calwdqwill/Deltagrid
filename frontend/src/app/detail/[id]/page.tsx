"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Shell } from "@/components/layout/Shell";
import { VenueCard } from "@/components/detail/VenueCard";
import { SpreadSummary } from "@/components/detail/SpreadSummary";
import { CalculationBreakdown } from "@/components/detail/CalculationBreakdown";
import { useLocale } from "@/hooks/useLocale";
import { fetchScannerDetail } from "@/lib/api";
import { ScannerRecord } from "@/types/scanner";
import { cn } from "@/lib/utils";

export default function DetailPage() {
  const params = useParams();
  const router = useRouter();
  const { t } = useLocale();
  const [record, setRecord] = useState<ScannerRecord | null>(null);
  const [loading, setLoading] = useState(true);

  const id = params.id as string;

  useEffect(() => {
    if (!id) return;
    fetchScannerDetail(id)
      .then((res) => setRecord(res.data.record))
      .catch(() => setRecord(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64 text-secondary-text">Loading...</div>
      </Shell>
    );
  }

  if (!record) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64 text-secondary-text">
          Record not found
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="max-w-3xl space-y-6">
        <button
          onClick={() => router.push("/")}
          className="inline-flex items-center gap-2 text-sm text-secondary-text hover:text-primary-text transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          {t.detail.back}
        </button>

        <div className="flex items-center gap-4">
          {record.iconUrl && (
            <img src={record.iconUrl} alt={record.symbol} className="w-16 h-16 rounded-full" />
          )}
          <div>
            <h1 className="text-3xl font-bold text-primary-text">{record.tokenName}</h1>
            <p className="text-lg text-secondary-text">{record.pair}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <VenueCard type="buy" venue={record.buyVenue} price={record.buyPrice} />
          <VenueCard type="sell" venue={record.sellVenue} price={record.sellPrice} />
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
          <div className="bg-gray-50 rounded-lg border border-border p-5 space-y-3">
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

        <div className="bg-white rounded-lg border border-border p-5 text-xs text-secondary-text space-y-2">
          <div className="flex justify-between py-1">
            <span>ID</span>
            <span className="font-medium text-primary-text">{record.id}</span>
          </div>
          <div className="flex justify-between py-1">
            <span>Data Status</span>
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
    </Shell>
  );
}
