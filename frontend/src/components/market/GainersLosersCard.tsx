"use client";

import Image from "next/image";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";

interface MarketCoin {
  id: string;
  name: string;
  symbol: string;
  image?: string;
  currentPrice?: number;
  priceChangePercentage24h?: number;
  marketCapRank?: number;
}

function CoinRow({ coin }: { coin: MarketCoin }) {
  const change = coin.priceChangePercentage24h ?? 0;
  const isPositive = change >= 0;

  return (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-row-hover transition-colors">
      {coin.image ? (
        <Image
          src={coin.image}
          alt={coin.name}
          width={32}
          height={32}
          className="rounded-full"
        />
      ) : (
        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold text-secondary-text">
          {coin.symbol?.slice(0, 2)}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-primary-text truncate">{coin.name}</div>
        <div className="text-xs text-secondary-text">{coin.symbol}</div>
      </div>
      <div className="text-right">
        <div className="text-sm font-medium text-primary-text">
          ${coin.currentPrice?.toLocaleString(undefined, { maximumFractionDigits: 4 })}
        </div>
        <div
          className={cn(
            "text-xs font-medium flex items-center justify-end gap-0.5",
            isPositive ? "text-emerald-600" : "text-red-600"
          )}
        >
          {isPositive ? (
            <ArrowUpRight className="w-3 h-3" />
          ) : (
            <ArrowDownRight className="w-3 h-3" />
          )}
          {Math.abs(change).toFixed(2)}%
        </div>
      </div>
    </div>
  );
}

export function GainersCard({ items }: { items: MarketCoin[] }) {
  const { t } = useLocale();
  return (
    <div className="bg-white rounded-xl border border-border p-4">
      <div className="flex items-center gap-2 mb-3">
        <ArrowUpRight className="w-5 h-5 text-emerald-600" />
        <h3 className="font-semibold text-primary-text">{t.market.topGainers}</h3>
      </div>
      <div className="space-y-1">
        {items.map((coin) => (
          <CoinRow key={coin.id} coin={coin} />
        ))}
        {items.length === 0 && (
          <div className="text-sm text-secondary-text py-4 text-center">No data</div>
        )}
      </div>
    </div>
  );
}

export function LosersCard({ items }: { items: MarketCoin[] }) {
  const { t } = useLocale();
  return (
    <div className="bg-white rounded-xl border border-border p-4">
      <div className="flex items-center gap-2 mb-3">
        <ArrowDownRight className="w-5 h-5 text-red-600" />
        <h3 className="font-semibold text-primary-text">{t.market.topLosers}</h3>
      </div>
      <div className="space-y-1">
        {items.map((coin) => (
          <CoinRow key={coin.id} coin={coin} />
        ))}
        {items.length === 0 && (
          <div className="text-sm text-secondary-text py-4 text-center">No data</div>
        )}
      </div>
    </div>
  );
}
