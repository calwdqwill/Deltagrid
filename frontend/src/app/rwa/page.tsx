"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { useLocale } from "@/hooks/useLocale";
import { useRwaAssets, useRwaCategories } from "@/hooks/useRwaAssets";
import { cn } from "@/lib/utils";

export default function RwaPage() {
  const router = useRouter();
  const { t } = useLocale();
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const { data: assets, isLoading } = useRwaAssets(selectedCategory);
  const { data: categories } = useRwaCategories();

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-primary-text">{t.rwa.title}</h2>
        </div>

        {/* Category filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory(undefined)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors",
              !selectedCategory
                ? "bg-accent-blue text-white border-accent-blue"
                : "bg-white text-secondary-text border-border hover:bg-row-hover"
            )}
          >
            All
          </button>
          {categories?.map((cat: any) => (
            <button
              key={cat.category}
              onClick={() => setSelectedCategory(cat.category)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors",
                selectedCategory === cat.category
                  ? "bg-accent-blue text-white border-accent-blue"
                  : "bg-white text-secondary-text border-border hover:bg-row-hover"
              )}
            >
              {cat.category} ({cat.count})
            </button>
          ))}
        </div>

        {/* Asset table */}
        <div className="bg-white rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted-bg">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-secondary-text">{t.rwa.columns.symbol}</th>
                  <th className="text-left px-4 py-3 font-semibold text-secondary-text">{t.rwa.columns.name}</th>
                  <th className="text-left px-4 py-3 font-semibold text-secondary-text">{t.rwa.columns.category}</th>
                  <th className="text-left px-4 py-3 font-semibold text-secondary-text">{t.rwa.columns.issuer}</th>
                  <th className="text-left px-4 py-3 font-semibold text-secondary-text">{t.rwa.columns.price}</th>
                  <th className="text-left px-4 py-3 font-semibold text-secondary-text">{t.rwa.columns.source}</th>
                  <th className="text-left px-4 py-3 font-semibold text-secondary-text">{t.rwa.columns.freshness}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {isLoading && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-secondary-text">
                      {t.rwa.loading}
                    </td>
                  </tr>
                )}
                {!isLoading && (!assets || assets.length === 0) && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-secondary-text">
                      {t.rwa.empty}
                    </td>
                  </tr>
                )}
                {assets?.map((asset: any) => (
                  <tr
                    key={asset.id}
                    className="hover:bg-row-hover transition-colors cursor-pointer"
                    onClick={() => router.push(`/rwa/${asset.id}`)}
                  >
                    <td className="px-4 py-3 font-medium text-primary-text">{asset.symbol}</td>
                    <td className="px-4 py-3 text-primary-text">{asset.name}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                        {asset.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-secondary-text">{asset.issuer || "—"}</td>
                    <td className="px-4 py-3 text-primary-text">
                      {asset.latestSnapshot?.priceUsd
                        ? `$${asset.latestSnapshot.priceUsd.toLocaleString()}`
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-secondary-text">
                      {asset.latestSnapshot?.source || "—"}
                    </td>
                    <td className="px-4 py-3">
                      {asset.latestSnapshot?.fetchedAt ? (
                        <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          Live
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-amber-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                          Stale
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Shell>
  );
}
