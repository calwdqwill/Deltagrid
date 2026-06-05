import { Shell } from "@/components/layout/Shell";
import {
  DonutChart,
  formatCompactCurrency,
  formatNumber,
  formatSigned,
  LinkButton,
  SegmentedControl,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveAssetDeepDive } from "@/lib/terminal/live-market";
import { Candle } from "@/types/terminal";

export const dynamic = "force-dynamic";

function CandleChart({ candles }: { candles: Candle[] }) {
  const width = 860;
  const height = 300;

  if (!candles.length) {
    return (
      <div className="flex h-full min-h-[300px] items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.02] text-xs text-slate-500">
        No OHLCV candles
      </div>
    );
  }

  const min = Math.min(...candles.map((candle) => candle.low));
  const max = Math.max(...candles.map((candle) => candle.high));
  const span = max - min || 1;
  const step = width / candles.length;
  const maxVolume = Math.max(...candles.map((candle) => candle.volume ?? 0), 1);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full" role="img">
      {[0, 1, 2, 3].map((line) => (
        <line
          key={line}
          x1="0"
          x2={width}
          y1={24 + line * 58}
          y2={24 + line * 58}
          stroke="rgba(148,163,184,0.12)"
        />
      ))}
      {candles.map((candle, index) => {
        const x = index * step + step / 2;
        const high = height - ((candle.high - min) / span) * 225 - 44;
        const low = height - ((candle.low - min) / span) * 225 - 44;
        const open = height - ((candle.open - min) / span) * 225 - 44;
        const close = height - ((candle.close - min) / span) * 225 - 44;
        const positive = candle.close >= candle.open;
        const y = Math.min(open, close);
        const bodyHeight = Math.max(Math.abs(close - open), 3);
        const volumeHeight = ((candle.volume ?? 0) / maxVolume) * 38;

        return (
          <g key={candle.time}>
            <line x1={x} x2={x} y1={high} y2={low} stroke={positive ? "#10B981" : "#F43F5E"} strokeWidth="1.5" />
            <rect
              x={x - Math.max(step * 0.28, 3)}
              y={y}
              width={Math.max(step * 0.56, 5)}
              height={bodyHeight}
              rx="2"
              fill={positive ? "#10B981" : "#F43F5E"}
            />
            <rect
              x={x - Math.max(step * 0.28, 3)}
              y={height - 34 - volumeHeight}
              width={Math.max(step * 0.56, 5)}
              height={volumeHeight}
              fill={positive ? "rgba(16,185,129,0.25)" : "rgba(244,63,94,0.25)"}
            />
          </g>
        );
      })}
    </svg>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-white/[0.06] bg-white/[0.02] px-3 py-4 text-xs text-slate-500">
      {label}
    </div>
  );
}

export default async function AssetsPage() {
  const live = await getLiveAssetDeepDive("SOL");
  const data = live.data;
  const asset = data.asset;

  const derivativeRows = data.derivatives.map((item) => [
    item.label,
    <span key="value" className="font-mono text-slate-100">
      {item.value}
    </span>,
    <span key="delta" className={toneText(item.tone)}>
      {item.delta ?? "-"}
    </span>,
  ]);

  const bidRows = data.orderBook.bids.map((level) => [
    <span key="price" className="font-mono text-emerald-300">
      {level.price.toFixed(2)}
    </span>,
    <span key="size" className="font-mono">
      {level.size.toLocaleString()}
    </span>,
  ]);

  const askRows = data.orderBook.asks.map((level) => [
    <span key="price" className="font-mono text-rose-300">
      {level.price.toFixed(2)}
    </span>,
    <span key="size" className="font-mono">
      {level.size.toLocaleString()}
    </span>,
  ]);

  const sourceRows = live.sourceRows.map(([source, status]) => [source, status]);

  return (
    <Shell>
      <div className="space-y-4">
        <TerminalPanel className="overflow-hidden">
          <div className="grid gap-4 xl:grid-cols-[1fr_1.4fr]">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-300 via-cyan-400 to-indigo-600 text-2xl font-bold text-white">
                {asset.symbol[0] ?? "?"}
              </div>
              <div>
                <div className="text-sm text-slate-500">Asset Deep Dive</div>
                <div className="text-3xl font-semibold text-white">{asset.name}</div>
                <div className="font-mono text-sm text-slate-500">{asset.symbol}</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div>
                <div className="text-xs text-slate-500">Price</div>
                <div className="mt-1 font-mono text-3xl font-semibold text-white">${formatNumber(asset.price)}</div>
                <div className={toneText(asset.change24h >= 0 ? "positive" : "negative")}>{formatSigned(asset.change24h)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Market Cap</div>
                <div className="mt-1 font-mono text-xl text-slate-100">{formatCompactCurrency(asset.marketCap)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">24h Volume</div>
                <div className="mt-1 font-mono text-xl text-slate-100">{formatCompactCurrency(asset.volume24h)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Open Interest</div>
                <div className="mt-1 font-mono text-xl text-slate-100">{formatCompactCurrency(asset.openInterest)}</div>
              </div>
            </div>
          </div>
        </TerminalPanel>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <SegmentedControl items={["Overview", "Derivatives", "Venues", "Liquidity", "Correlations", "Related Opportunities"]} active="Overview" />
          <div className="flex items-center gap-2">
            <StatusBadge label={live.statusLabel} tone={live.statusTone} />
            <LinkButton href="/strategy-lab">Backtest SOL</LinkButton>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.35fr_0.65fr]">
          <TerminalPanel title="SOL / USD Chart" caption={data.candles.length ? "Binance 1m candles from PostgreSQL" : "No SOL OHLCV rows in PostgreSQL yet"}>
            <div className="h-[360px]">
              <CandleChart candles={data.candles} />
            </div>
          </TerminalPanel>

          <TerminalPanel title="Key Metrics">
            <div className="space-y-3">
              {data.keyMetrics.map((metric) => (
                <div key={metric.label} className="flex items-center justify-between border-b border-white/[0.06] pb-2">
                  <span className="text-sm text-slate-500">{metric.label}</span>
                  <span className={`font-mono text-sm ${toneText(metric.tone)}`}>{metric.value}</span>
                </div>
              ))}
            </div>
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.95fr_1fr]">
          <TerminalPanel title="Derivatives Overview">
            <TerminalTable columns={["Metric", "Value", "Delta"]} rows={derivativeRows} />
          </TerminalPanel>

          <TerminalPanel title="Venue Breakdown (Volume 24h)">
            {data.venueBreakdown.length ? (
              <DonutChart
                data={data.venueBreakdown}
                center={
                  <div>
                    <div className="font-mono text-lg font-semibold text-white">{formatCompactCurrency(asset.perpVolume)}</div>
                    <div className="text-xs text-slate-500">Total</div>
                  </div>
                }
              />
            ) : (
              <EmptyState label="Live venue breakdown endpoint is not connected yet" />
            )}
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.95fr_1fr]">
          <TerminalPanel title="Order Book (Binance / SOLUSDT)">
            {bidRows.length || askRows.length ? (
              <div className="grid grid-cols-2 gap-3">
                <TerminalTable columns={["Bid", "Size"]} rows={bidRows} />
                <TerminalTable columns={["Ask", "Size"]} rows={askRows} />
              </div>
            ) : (
              <EmptyState label="Live order book endpoint is not connected yet" />
            )}
          </TerminalPanel>

          <TerminalPanel title="Liquidations (24h)">
            {data.liquidations.byVenue.length ? (
              <div className="space-y-4">
                <div>
                  <div className="mb-1 flex justify-between text-xs text-slate-500">
                    <span>Longs</span>
                    <span>{formatCompactCurrency(data.liquidations.longUsd)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06]">
                    <div className="h-full rounded-full bg-emerald-400" style={{ width: "31.2%" }} />
                  </div>
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-xs text-slate-500">
                    <span>Shorts</span>
                    <span>{formatCompactCurrency(data.liquidations.shortUsd)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06]">
                    <div className="h-full rounded-full bg-rose-400" style={{ width: "84%" }} />
                  </div>
                </div>
                <DonutChart data={data.liquidations.byVenue} center={<div className="font-mono text-sm text-white">24h</div>} />
              </div>
            ) : (
              <EmptyState label="Live liquidations endpoint is not connected yet" />
            )}
          </TerminalPanel>
        </div>

        <TerminalPanel title="Live Sources">
          <TerminalTable columns={["Source", "Status"]} rows={sourceRows} />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
