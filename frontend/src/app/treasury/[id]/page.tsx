"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { Shell } from "@/components/layout/Shell";
import { useLocale } from "@/hooks/useLocale";
import { useTreasuryEntity } from "@/hooks/useTreasuryEntity";

export default function TreasuryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useLocale();
  const { data: entity, isLoading } = useTreasuryEntity(id);

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link
            href="/treasury"
            className="inline-flex items-center gap-1.5 text-sm text-secondary-text hover:text-primary-text transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Treasury
          </Link>
        </div>

        {isLoading && (
          <div className="text-center text-secondary-text py-12">{t.treasury.loading}</div>
        )}

        {!isLoading && !entity && (
          <div className="text-center text-secondary-text py-12">Entity not found.</div>
        )}

        {entity && (
          <div className="space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold text-primary-text">{entity.name}</h1>
                <div className="flex flex-wrap gap-2 mt-2">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700 capitalize">
                    {entity.entityType}
                  </span>
                  {entity.ticker && (
                    <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                      {entity.ticker}
                    </span>
                  )}
                </div>
              </div>
              {entity.websiteUrl && (
                <a
                  href={entity.websiteUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium border border-border hover:bg-row-hover transition-colors"
                >
                  Website
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>

            {entity.description && (
              <p className="text-sm text-secondary-text">{entity.description}</p>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-xl border border-border p-4 space-y-3">
                <h3 className="font-semibold text-primary-text">Company Info</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-secondary-text">Sector</span>
                    <span className="text-primary-text">{entity.sector || "—"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondary-text">Ticker</span>
                    <span className="text-primary-text">{entity.ticker || "—"}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-border p-4 space-y-3">
                <h3 className="font-semibold text-primary-text">Latest Treasury Snapshot</h3>
                {entity.latestSnapshot ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-secondary-text">BTC Holdings</span>
                      <span className="text-primary-text">
                        {entity.latestSnapshot.btcHoldings != null
                          ? `${entity.latestSnapshot.btcHoldings.toLocaleString()} BTC`
                          : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">BTC Value</span>
                      <span className="text-primary-text">
                        {entity.latestSnapshot.btcValueUsd != null
                          ? `$${entity.latestSnapshot.btcValueUsd.toLocaleString()}`
                          : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">BTC / Share</span>
                      <span className="text-primary-text">
                        {entity.latestSnapshot.btcPerShare != null
                          ? entity.latestSnapshot.btcPerShare.toFixed(6)
                          : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Source</span>
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        {entity.latestSnapshot.source}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Quality</span>
                      <span className="text-primary-text capitalize">{entity.latestSnapshot.sourceQuality}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Report Date</span>
                      <span className="text-primary-text">{entity.latestSnapshot.reportDate || "—"}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-secondary-text">No snapshot data available.</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Shell>
  );
}
