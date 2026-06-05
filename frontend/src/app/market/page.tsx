import { Shell } from "@/components/layout/Shell";
import {
  BarChart,
  formatCompactCurrency,
  formatNumber,
  formatSigned,
  Heatmap,
  KpiStrip,
  LineChart,
  Sparkline,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveMarketOverview } from "@/lib/terminal/live-market";

export const dynamic = "force-dynamic";

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-white/[0.06] bg-white/[0.02] px-3 py-4 text-xs text-slate-500">
      {label}
    </div>
  );
}

export default async function MarketPage() {
  const live = await getLiveMarketOverview();
  const data = live.data;
  const latestFearGreed = live.fearGreed[0];

  const assetRows = data.topAssets.map((asset, index) => [
    <span key="rank" className="font-mono text-slate-500">
      {index + 1}
    </span>,
    <div key="asset" className="flex items-center gap-2">
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-amber-300/80 to-indigo-500/80 text-[10px] font-bold text-white">
        {asset.symbol[0]}
      </span>
      <div>
        <div className="font-medium text-slate-100">{asset.name}</div>
        <div className="font-mono text-[11px] text-slate-500">{asset.symbol}</div>
      </div>
    </div>,
    <span key="price" className="font-mono text-slate-200">
      {asset.price >= 100 ? `$${formatNumber(asset.price)}` : `$${asset.price.toFixed(4)}`}
    </span>,
    <span key="24h" className={toneText(asset.change24h >= 0 ? "positive" : "negative")}>
      {formatSigned(asset.change24h)}
    </span>,
    <span key="7d" className={toneText(asset.change7d >= 0 ? "positive" : "negative")}>
      {formatSigned(asset.change7d)}
    </span>,
    <span key="cap" className="font-mono">
      {formatCompactCurrency(asset.marketCap)}
    </span>,
    <span key="vol" className="font-mono">
      {formatCompactCurrency(asset.volume24h)}
    </span>,
    <span key="ratio" className="font-mono">
      {asset.volumeToMarketCap.toFixed(2)}%
    </span>,
    <Sparkline
      key="spark"
      data={asset.sparkline}
      color={asset.change24h >= 0 ? "#10B981" : "#F43F5E"}
      className="h-8 w-24"
    />,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">
              Market Overview
            </div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Command Center</h1>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge label={live.statusLabel} tone={live.statusTone} />
            <StatusBadge label="No mock fallback" tone="neutral" />
          </div>
        </div>

        <KpiStrip metrics={data.kpis} />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.25fr_0.9fr]">
          <TerminalPanel title="Market Heatmap" caption="Global spot market leaders by cap and 24h move">
            <Heatmap items={data.heatmap} />
          </TerminalPanel>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-1">
            <TerminalPanel title="Top Gainers (24h)">
              <div className="space-y-3">
                {data.topGainers.length ? (
                  data.topGainers.map((asset) => (
                    <div key={asset.symbol} className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-slate-600">{asset.rank}</span>
                        <span className="font-medium text-slate-100">{asset.symbol}</span>
                        <span className="text-xs text-slate-500">{asset.name}</span>
                      </div>
                      <span className="font-mono text-sm text-emerald-400">{formatSigned(asset.change24h)}</span>
                    </div>
                  ))
                ) : (
                  <EmptyState label="No gainers returned by market API" />
                )}
              </div>
            </TerminalPanel>

            <TerminalPanel title="Top Losers (24h)">
              <div className="space-y-3">
                {data.topLosers.length ? (
                  data.topLosers.map((asset) => (
                    <div key={asset.symbol} className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-slate-600">{asset.rank}</span>
                        <span className="font-medium text-slate-100">{asset.symbol}</span>
                        <span className="text-xs text-slate-500">{asset.name}</span>
                      </div>
                      <span className="font-mono text-sm text-rose-400">{formatSigned(asset.change24h)}</span>
                    </div>
                  ))
                ) : (
                  <EmptyState label="No losers returned by market API" />
                )}
              </div>
            </TerminalPanel>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          {[data.btcOverview, data.ethOverview].map((snapshot) => (
            <TerminalPanel key={snapshot.symbol} title={`${snapshot.symbol} Overview`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-mono text-3xl font-semibold text-white">
                    ${formatNumber(snapshot.price)}
                  </div>
                  <div className={toneText(snapshot.change24h >= 0 ? "positive" : "negative")}>
                    {formatSigned(snapshot.change24h)}
                  </div>
                </div>
                <div className="text-right text-xs text-slate-500">
                  <div>Dominance</div>
                  <div className="mt-1 font-mono text-base text-slate-200">{snapshot.dominance?.toFixed(2)}%</div>
                </div>
              </div>
              <div className="mt-4 h-32">
                <LineChart
                  data={snapshot.sparkline.map((value, index) => ({ label: String(index), value }))}
                  color={snapshot.change24h >= 0 ? "#10B981" : "#F43F5E"}
                  height={140}
                />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-md bg-white/[0.035] p-2">
                  <div className="text-slate-500">Market Cap</div>
                  <div className="mt-1 font-mono text-slate-200">{formatCompactCurrency(snapshot.marketCap)}</div>
                </div>
                <div className="rounded-md bg-white/[0.035] p-2">
                  <div className="text-slate-500">24h Volume</div>
                  <div className="mt-1 font-mono text-slate-200">{formatCompactCurrency(snapshot.volume24h)}</div>
                </div>
              </div>
            </TerminalPanel>
          ))}

          <TerminalPanel title="Market Breadth" caption="Broad participation snapshot">
            <div className="mb-3">
              <div className="font-mono text-3xl font-semibold text-emerald-400">
                {data.marketBreadth.advancing}%
              </div>
              <div className="text-sm text-slate-500">Advancing</div>
            </div>
            <div className="mb-4 grid grid-cols-3 gap-2 text-xs">
              <div className="rounded-md bg-emerald-500/10 p-2 text-emerald-300">
                Advancing {data.marketBreadth.advancing}%
              </div>
              <div className="rounded-md bg-slate-500/10 p-2 text-slate-300">
                Neutral {data.marketBreadth.neutral}%
              </div>
              <div className="rounded-md bg-rose-500/10 p-2 text-rose-300">
                Declining {data.marketBreadth.declining}%
              </div>
            </div>
            <BarChart data={data.marketBreadth.histogram} colors={["#10B981", "#06B6D4", "#F97316"]} />
          </TerminalPanel>
        </div>

        <TerminalPanel title="Fear & Greed Index" caption="Alternative.me latest 7 days">
          <div className="grid gap-4 lg:grid-cols-[0.35fr_1fr]">
            <div className="rounded-md border border-white/[0.06] bg-white/[0.03] p-4">
              <div
                className={`font-mono text-5xl font-semibold ${toneText(
                  latestFearGreed && latestFearGreed.value <= 40 ? "negative" : "warning"
                )}`}
              >
                {latestFearGreed ? latestFearGreed.value : "No data"}
              </div>
              <div className="mt-2 text-sm text-slate-400">
                {latestFearGreed?.classification ?? "Provider returned empty data"}
              </div>
            </div>
            <div className="space-y-2">
              {live.fearGreed.length ? (
                live.fearGreed.map((point) => {
                  const date = new Date(point.timestamp * 1000).toISOString().slice(0, 10);
                  return (
                    <div key={point.timestamp} className="grid grid-cols-[88px_1fr_48px] items-center gap-3 text-xs">
                      <span className="font-mono text-slate-500">{date}</span>
                      <div className="h-2 rounded-full bg-white/[0.06]">
                        <div
                          className="h-full rounded-full bg-amber-300"
                          style={{ width: `${Math.max(2, Math.min(point.value, 100))}%` }}
                        />
                      </div>
                      <span className="text-right font-mono text-slate-300">{point.value}</span>
                    </div>
                  );
                })
              ) : (
                <EmptyState label="Fear & Greed provider returned no rows" />
              )}
            </div>
          </div>
        </TerminalPanel>

        <TerminalPanel title="Top Assets" caption="Spot market table with OI and perp volume context">
          <TerminalTable
            columns={["#", "Asset", "Price", "24H", "7D", "Market Cap", "24H Volume", "Vol / MCap", "7D"]}
            rows={assetRows}
          />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
