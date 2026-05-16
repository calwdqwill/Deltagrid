"use client";

import { Globe, DollarSign, Activity, Bitcoin, Landmark, Coins } from "lucide-react";
import { useLocale } from "@/hooks/useLocale";

interface GlobalStats {
  totalMarketCapUsd?: number;
  totalVolume24hUsd?: number;
  btcDominance?: number;
  ethDominance?: number;
  activeCryptocurrencies?: number;
  updatedAt?: string;
}

function StatItem({
  icon: Icon,
  label,
  value,
  format = "number",
}: {
  icon: React.ElementType;
  label: string;
  value?: number;
  format?: "number" | "percent" | "currency";
}) {
  const formatted =
    value === undefined
      ? "—"
      : format === "percent"
      ? `${value.toFixed(1)}%`
      : format === "currency"
      ? `$${(value / 1e9).toFixed(1)}B`
      : value.toLocaleString();

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <div className="p-2 rounded-lg bg-white">
        <Icon className="w-4 h-4 text-accent-blue" />
      </div>
      <div>
        <div className="text-xs text-secondary-text">{label}</div>
        <div className="text-sm font-semibold text-primary-text">{formatted}</div>
      </div>
    </div>
  );
}

export function GlobalStatsCard({ stats }: { stats: GlobalStats | null }) {
  const { t } = useLocale();

  return (
    <div className="bg-white rounded-xl border border-border p-4">
      <div className="flex items-center gap-2 mb-3">
        <Globe className="w-5 h-5 text-accent-blue" />
        <h3 className="font-semibold text-primary-text">{t.market.globalStats}</h3>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <StatItem
          icon={DollarSign}
          label={t.market.marketCap}
          value={stats?.totalMarketCapUsd}
          format="currency"
        />
        <StatItem
          icon={Activity}
          label={t.market.volume24h}
          value={stats?.totalVolume24hUsd}
          format="currency"
        />
        <StatItem
          icon={Bitcoin}
          label={t.market.btcDominance}
          value={stats?.btcDominance}
          format="percent"
        />
        <StatItem
          icon={Landmark}
          label={t.market.ethDominance}
          value={stats?.ethDominance}
          format="percent"
        />
        <StatItem
          icon={Coins}
          label={t.market.activeCryptos}
          value={stats?.activeCryptocurrencies}
          format="number"
        />
      </div>
    </div>
  );
}
