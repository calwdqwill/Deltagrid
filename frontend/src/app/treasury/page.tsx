"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { useLocale } from "@/hooks/useLocale";
import { useTreasuryEntities, useBtcHoldings, useTokenizationPlatforms } from "@/hooks/useTreasuryEntities";
import { cn } from "@/lib/utils";

export default function TreasuryPage() {
  const router = useRouter();
  const { t } = useLocale();
  const [tab, setTab] = useState<"companies" | "platforms">("companies");
  const { data: entities, isLoading: entitiesLoading } = useTreasuryEntities("public_company");
  const { data: btcHoldings } = useBtcHoldings();
  const { data: platforms, isLoading: platformsLoading } = useTokenizationPlatforms();

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-primary-text">{t.treasury.title}</h2>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-border">
          <button
            onClick={() => setTab("companies")}
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
              tab === "companies"
                ? "border-accent-blue text-accent-blue"
                : "border-transparent text-secondary-text hover:text-primary-text"
            )}
          >
            {t.treasury.companies}
          </button>
          <button
            onClick={() => setTab("platforms")}
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
              tab === "platforms"
                ? "border-accent-blue text-accent-blue"
                : "border-transparent text-secondary-text hover:text-primary-text"
            )}
          >
            {t.treasury.platforms}
          </button>
        </div>

        {/* Companies tab */}
        {tab === "companies" && (
          <div className="space-y-6">
            {/* BTC Holdings summary */}
            {btcHoldings && btcHoldings.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {btcHoldings.slice(0, 4).map((row: any) => (
                  <div key={row.entityId} className="bg-white rounded-xl border border-border p-4">
                    <div className="text-sm text-secondary-text">{row.name}</div>
                    <div className="text-xl font-bold text-primary-text mt-1">
                      {row.btcHoldings !== null ? `${row.btcHoldings.toLocaleString()} BTC` : "—"}
                    </div>
                    <div className="text-xs text-secondary-text mt-1">
                      {row.btcValueUsd !== null ? `$${(row.btcValueUsd / 1e9).toFixed(2)}B` : "—"}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Companies table */}
            <div className="bg-white rounded-xl border border-border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted-bg">
                    <tr>
                      <th className="text-left px-4 py-3 font-semibold text-secondary-text">Name</th>
                      <th className="text-left px-4 py-3 font-semibold text-secondary-text">Ticker</th>
                      <th className="text-left px-4 py-3 font-semibold text-secondary-text">Sector</th>
                      <th className="text-left px-4 py-3 font-semibold text-secondary-text">BTC Holdings</th>
                      <th className="text-left px-4 py-3 font-semibold text-secondary-text">Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {entitiesLoading && (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-secondary-text">
                          {t.treasury.loading}
                        </td>
                      </tr>
                    )}
                    {!entitiesLoading && (!entities || entities.length === 0) && (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-secondary-text">
                          {t.treasury.empty}
                        </td>
                      </tr>
                    )}
                    {entities?.map((entity: any) => (
                      <tr
                        key={entity.id}
                        className="hover:bg-row-hover transition-colors cursor-pointer"
                        onClick={() => router.push(`/treasury/${entity.id}`)}
                      >
                        <td className="px-4 py-3 font-medium text-primary-text">{entity.name}</td>
                        <td className="px-4 py-3 text-secondary-text">{entity.ticker || "—"}</td>
                        <td className="px-4 py-3 text-secondary-text">{entity.sector || "—"}</td>
                        <td className="px-4 py-3 text-primary-text">
                          {entity.latestSnapshot?.btcHoldings
                            ? `${entity.latestSnapshot.btcHoldings.toLocaleString()} BTC`
                            : "—"}
                        </td>
                        <td className="px-4 py-3 text-secondary-text">
                          {entity.latestSnapshot?.source || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Platforms tab */}
        {tab === "platforms" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {platformsLoading && (
              <div className="col-span-full text-center text-secondary-text py-8">{t.treasury.loading}</div>
            )}
            {!platformsLoading && (!platforms || platforms.length === 0) && (
              <div className="col-span-full text-center text-secondary-text py-8">{t.treasury.empty}</div>
            )}
            {platforms?.map((platform: any) => (
              <div key={platform.id} className="bg-white rounded-xl border border-border p-4 space-y-2">
                <div className="font-semibold text-primary-text">{platform.name}</div>
                <div className="text-sm text-secondary-text">{platform.description || "—"}</div>
                <div className="flex flex-wrap gap-2 pt-2">
                  {platform.category && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                      {platform.category}
                    </span>
                  )}
                  {platform.blockchain && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                      {platform.blockchain}
                    </span>
                  )}
                </div>
                {platform.tvlUsd !== null && (
                  <div className="text-sm text-primary-text pt-1">
                    TVL: ${platform.tvlUsd.toLocaleString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
