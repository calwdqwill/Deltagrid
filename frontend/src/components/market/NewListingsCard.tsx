"use client";

import Image from "next/image";
import { Sparkles } from "lucide-react";
import { useLocale } from "@/hooks/useLocale";

interface NewListingItem {
  id: string;
  name: string;
  symbol: string;
  thumb?: string;
  marketCapRank?: number;
  priceBtc?: number;
  score?: number;
}

export function NewListingsCard({ items }: { items: NewListingItem[] }) {
  const { t } = useLocale();

  return (
    <div className="bg-white rounded-xl border border-border p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-5 h-5 text-accent-blue" />
        <h3 className="font-semibold text-primary-text">{t.market.newListings}</h3>
      </div>
      <div className="space-y-2">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-row-hover transition-colors"
          >
            {item.thumb ? (
              <Image
                src={item.thumb}
                alt={item.name}
                width={32}
                height={32}
                className="rounded-full"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold text-secondary-text">
                {item.symbol?.slice(0, 2)}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="font-medium text-primary-text truncate">{item.name}</div>
              <div className="text-xs text-secondary-text">{item.symbol}</div>
            </div>
            {item.marketCapRank && (
              <div className="text-xs font-medium text-secondary-text">
                #{item.marketCapRank}
              </div>
            )}
          </div>
        ))}
        {items.length === 0 && (
          <div className="text-sm text-secondary-text py-4 text-center">No data</div>
        )}
      </div>
    </div>
  );
}
