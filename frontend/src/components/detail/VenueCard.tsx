"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { formatPrice } from "@/lib/utils";
import { useLocale } from "@/hooks/useLocale";

interface VenueCardProps {
  type: "buy" | "sell";
  venue: string;
  price: number;
}

export function VenueCard({ type, venue, price }: VenueCardProps) {
  const { t } = useLocale();
  const isBuy = type === "buy";

  return (
    <div className="bg-white rounded-lg border border-border p-4 shadow-soft">
      <div className="flex items-center gap-2 mb-3">
        <div
          className={`p-1.5 rounded-md ${isBuy ? "bg-emerald-50" : "bg-red-50"}`}
        >
          {isBuy ? (
            <ArrowDownRight className="w-4 h-4 text-positive" />
          ) : (
            <ArrowUpRight className="w-4 h-4 text-negative" />
          )}
        </div>
        <span className="text-xs font-medium uppercase tracking-wider text-secondary-text">
          {isBuy ? t.detail.buyCard : t.detail.sellCard}
        </span>
      </div>
      <div className="text-sm text-secondary-text mb-1">{venue}</div>
      <div className="text-2xl font-bold text-primary-text tabular-nums">
        {formatPrice(price)}
      </div>
    </div>
  );
}
