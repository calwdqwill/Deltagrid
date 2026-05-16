"use client";

import { Shell } from "@/components/layout/Shell";
import { TrendingCard } from "@/components/market/TrendingCard";
import { GainersCard, LosersCard } from "@/components/market/GainersLosersCard";
import { GlobalStatsCard } from "@/components/market/GlobalStatsCard";
import { FearGreedCard } from "@/components/market/FearGreedCard";
import { NewListingsCard } from "@/components/market/NewListingsCard";
import { FundingRatesCard } from "@/components/market/FundingRatesCard";
import { useMarketData } from "@/hooks/useMarket";
import { useLocale } from "@/hooks/useLocale";
import { useRealtime } from "@/hooks/useRealtime";
import { RealtimeIndicator } from "@/components/market/RealtimeIndicator";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

export default function MarketPage() {
  const { t } = useLocale();
  const { trending, gainers, losers, global, fearGreed, newListings, fundingRates, isLoading, refetch } = useMarketData(60000);
  useRealtime();

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-primary-text">{t.market.title}</h1>
            <RealtimeIndicator />
          </div>
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className={cn(
              "inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border border-border hover:bg-row-hover transition-colors",
              isLoading && "opacity-50 cursor-not-allowed"
            )}
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <TrendingCard items={trending as any[]} />
          <GainersCard items={gainers as any[]} />
          <LosersCard items={losers as any[]} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div>
            <FearGreedCard data={fearGreed as any[]} />
          </div>
          <div>
            <NewListingsCard items={newListings as any[]} />
          </div>
          <div>
            <FundingRatesCard items={fundingRates as any[]} />
          </div>
          <div>
            <GlobalStatsCard stats={global} />
          </div>
        </div>
      </div>
    </Shell>
  );
}
