"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { KpiCards } from "@/components/scanner/KpiCards";
import { ScannerTabs } from "@/components/scanner/ScannerTabs";
import { ScannerFilters } from "@/components/scanner/ScannerFilters";
import { ScannerTable } from "@/components/scanner/ScannerTable";
import { RefreshControl } from "@/components/scanner/RefreshControl";
import { DetailDrawer } from "@/components/detail/DetailDrawer";
import OrderIntentModal from "@/components/execution/OrderIntentModal";
import { useScannerData } from "@/hooks/useScanner";
import { usePreferences } from "@/hooks/usePreferences";
import { useScannerStore } from "@/stores/scannerStore";
import { useRealtime } from "@/hooks/useRealtime";
import { RealtimeIndicator } from "@/components/market/RealtimeIndicator";
import { ScannerRecord } from "@/types/scanner";

export default function ScannerPage() {
  const { preferences } = usePreferences();
  const { data, isLoading } = useScannerStore();
  const refreshInterval = preferences?.refreshIntervalSec || 60;
  useRealtime();

  const [countdown, setCountdown] = useState(refreshInterval);
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);
  const [tradeRecord, setTradeRecord] = useState<ScannerRecord | null>(null);

  // Refetch trigger
  const query = useScannerData(refreshInterval);

  useEffect(() => {
    setCountdown(refreshInterval);
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          query.refetch();
          return refreshInterval;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [refreshInterval, query]);

  const handleOpenTrade = (record: ScannerRecord) => {
    setTradeRecord(record);
    setIsTradeModalOpen(true);
  };

  return (
    <Shell>
      <div className="space-y-4">
        <KpiCards />

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ScannerTabs />
            <RealtimeIndicator />
          </div>
          <RefreshControl onRefresh={() => query.refetch()} countdown={countdown} />
        </div>

        <ScannerFilters />

        {data?.meta.isFallback && (
          <div className="px-4 py-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-800">
            Using fallback/mock data. Add a CoinGecko API key in backend .env for live data.
          </div>
        )}

        <ScannerTable onOpenTrade={handleOpenTrade} />
      </div>

      <DetailDrawer />

      <OrderIntentModal
        isOpen={isTradeModalOpen}
        onClose={() => setIsTradeModalOpen(false)}
        defaultSymbol={tradeRecord?.symbol}
        defaultSide={tradeRecord && tradeRecord.buyPrice < tradeRecord.sellPrice ? "buy" : "sell"}
      />
    </Shell>
  );
}
