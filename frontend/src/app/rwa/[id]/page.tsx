"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { Shell } from "@/components/layout/Shell";
import { useLocale } from "@/hooks/useLocale";
import { useRwaAsset } from "@/hooks/useRwaAsset";

export default function RwaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useLocale();
  const { data: asset, isLoading } = useRwaAsset(id);

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link
            href="/rwa"
            className="inline-flex items-center gap-1.5 text-sm text-secondary-text hover:text-primary-text transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to RWA
          </Link>
        </div>

        {isLoading && (
          <div className="text-center text-secondary-text py-12">{t.rwa.loading}</div>
        )}

        {!isLoading && !asset && (
          <div className="text-center text-secondary-text py-12">Asset not found.</div>
        )}

        {asset && (
          <div className="space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold text-primary-text">
                  {asset.name} ({asset.symbol})
                </h1>
                <div className="flex flex-wrap gap-2 mt-2">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700">
                    {asset.category}
                  </span>
                  {asset.isExecutable === false && (
                    <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-700">
                      Informational Only
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-xl border border-border p-4 space-y-3">
                <h3 className="font-semibold text-primary-text">Asset Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-secondary-text">Issuer</span>
                    <span className="text-primary-text">{asset.issuer || "—"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondary-text">Blockchain</span>
                    <span className="text-primary-text">{asset.blockchain || "—"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondary-text">Contract</span>
                    <span className="text-primary-text font-mono text-xs">
                      {asset.contractAddress ? (
                        <a
                          href={`https://etherscan.io/token/${asset.contractAddress}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-accent-blue hover:underline"
                        >
                          {asset.contractAddress.slice(0, 6)}...{asset.contractAddress.slice(-4)}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        "—"
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondary-text">Decimals</span>
                    <span className="text-primary-text">{asset.decimals ?? "—"}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-border p-4 space-y-3">
                <h3 className="font-semibold text-primary-text">Latest Snapshot</h3>
                {asset.latestSnapshot ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Price</span>
                      <span className="text-primary-text">
                        {asset.latestSnapshot.priceUsd != null
                          ? `$${asset.latestSnapshot.priceUsd.toLocaleString()}`
                          : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">NAV</span>
                      <span className="text-primary-text">
                        {asset.latestSnapshot.navUsd != null
                          ? `$${asset.latestSnapshot.navUsd.toLocaleString()}`
                          : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Market Cap</span>
                      <span className="text-primary-text">
                        {asset.latestSnapshot.marketCapUsd != null
                          ? `$${asset.latestSnapshot.marketCapUsd.toLocaleString()}`
                          : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Source</span>
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        {asset.latestSnapshot.source}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Quality</span>
                      <span className="text-primary-text capitalize">{asset.latestSnapshot.sourceQuality}</span>
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
