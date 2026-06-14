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
import { TRACKED_SYMBOLS } from "@/lib/terminal/live-streams";
import { Candle } from "@/types/terminal";

export const dynamic = "force-dynamic";

function normalizeSymbol(value?: string): string {
  const normalized = value?.toUpperCase();
  return TRACKED_SYMBOLS.includes(normalized as (typeof TRACKED_SYMBOLS)[number]) ? normalized ?? "SOL" : "SOL";
}

function formatAssetPrice(value: number): string {
  return value >= 100 ? `$${formatNumber(value)}` : `$${value.toFixed(4)}`;
}

function CandleChart({ candles }: { candles: Candle[] }) {
  const width = 860;
  const height = 300;
  const padding = { top: 18, right: 74, bottom: 34, left: 10 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

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
  const step = plotWidth / candles.length;
  const maxVolume = Math.max(...candles.map((candle) => candle.volume ?? 0), 1);
  const latest = candles[candles.length - 1];
  const axisTicks = [max, min + span * 0.66, min + span * 0.33, min];
  const xTicks = [
    candles[0],
    candles[Math.floor(candles.length / 2)],
    candles[candles.length - 1],
  ].filter(Boolean);

  const yForPrice = (price: number) => padding.top + plotHeight - ((price - min) / span) * plotHeight;
  const labelForTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return Number.isNaN(date.getTime()) ? String(timestamp) : date.toISOString().slice(11, 16);
  };

  return (
    <div className="flex h-full min-h-[300px] flex-col">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-mono text-slate-300">Last {formatAssetPrice(latest.close)}</span>
        <span className="font-mono text-slate-500">
          Range {formatAssetPrice(min)} - {formatAssetPrice(max)}
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="min-h-0 w-full flex-1" role="img">
        {axisTicks.map((tick, index) => {
          const y = yForPrice(tick);
          return (
            <g key={`${tick}-${index}`}>
              <line x1={padding.left} x2={padding.left + plotWidth} y1={y} y2={y} stroke="rgba(148,163,184,0.12)" />
              <text x={width - 6} y={y + 4} textAnchor="end" className="fill-slate-500 text-[10px]">
                {formatAssetPrice(tick)}
              </text>
            </g>
          );
        })}
        {candles.map((candle, index) => {
          const x = padding.left + index * step + step / 2;
          const bodyWidth = Math.max(Math.min(step * 0.62, 8), 2);
          const high = yForPrice(candle.high);
          const low = yForPrice(candle.low);
          const open = yForPrice(candle.open);
          const close = yForPrice(candle.close);
          const positive = candle.close >= candle.open;
          const y = Math.min(open, close);
          const bodyHeight = Math.max(Math.abs(close - open), 3);
          const volumeHeight = ((candle.volume ?? 0) / maxVolume) * 34;
          const tooltip = [
            `${labelForTime(candle.time)}`,
            `Open ${formatAssetPrice(candle.open)}`,
            `High ${formatAssetPrice(candle.high)}`,
            `Low ${formatAssetPrice(candle.low)}`,
            `Close ${formatAssetPrice(candle.close)}`,
            `Volume ${formatCompactCurrency(candle.volume ?? 0)}`,
          ].join(" | ");

          return (
            <g key={candle.time}>
              <title>{tooltip}</title>
              <line x1={x} x2={x} y1={high} y2={low} stroke={positive ? "#10B981" : "#F43F5E"} strokeWidth="1.5" />
              <rect
                x={x - bodyWidth / 2}
                y={y}
                width={bodyWidth}
                height={bodyHeight}
                rx="2"
                fill={positive ? "#10B981" : "#F43F5E"}
              />
              <rect
                x={x - bodyWidth / 2}
                y={height - 34 - volumeHeight}
                width={bodyWidth}
                height={volumeHeight}
                fill={positive ? "rgba(16,185,129,0.25)" : "rgba(244,63,94,0.25)"}
              />
              <rect
                x={x - step / 2}
                y={padding.top}
                width={Math.max(step, 1)}
                height={plotHeight}
                fill="transparent"
                pointerEvents="all"
              >
                <title>{tooltip}</title>
              </rect>
            </g>
          );
        })}
        {xTicks.map((tick) => {
          const index = candles.indexOf(tick);
          const x = padding.left + index * step + step / 2;
          return (
            <text key={`${tick.time}-${index}`} x={x} y={height - 8} textAnchor={index === 0 ? "start" : index === candles.length - 1 ? "end" : "middle"} className="fill-slate-500 text-[10px]">
              {labelForTime(tick.time)}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-white/[0.06] bg-white/[0.02] px-3 py-4 text-xs text-slate-500">
      {label}
    </div>
  );
}

export default async function AssetsPage({ searchParams }: { searchParams?: { symbol?: string } }) {
  const symbol = normalizeSymbol(searchParams?.symbol);
  const live = await getLiveAssetDeepDive(symbol);
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
  const liquidationTotal = data.liquidations.longUsd + data.liquidations.shortUsd;
  const longLiquidationWidth = liquidationTotal > 0 ? (data.liquidations.longUsd / liquidationTotal) * 100 : 0;
  const shortLiquidationWidth = liquidationTotal > 0 ? (data.liquidations.shortUsd / liquidationTotal) * 100 : 0;
  const okxPair = `${asset.symbol}-USDT-SWAP`;

  return (
    <Shell>
      <div className="space-y-4">
        <TerminalPanel className="overflow-hidden">
          <div className="grid gap-4 xl:grid-cols-[1fr_1.4fr]">
            <div className="flex items-center gap-4">
              {asset.image ? (
                <img src={asset.image} alt="" className="h-16 w-16 rounded-2xl" />
              ) : (
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-300 via-cyan-400 to-indigo-600 text-2xl font-bold text-white">
                  {asset.symbol[0] ?? "?"}
                </div>
              )}
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
          <SegmentedControl
            items={TRACKED_SYMBOLS.map((item) => ({ label: item, href: `/assets?symbol=${item}` }))}
            active={asset.symbol}
          />
          <div className="flex items-center gap-2">
            <StatusBadge label={live.statusLabel} tone={live.statusTone} />
            <LinkButton href="/strategy-lab">Backtest {asset.symbol}</LinkButton>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.35fr_0.65fr]">
          <TerminalPanel title={`${asset.symbol} / USD Chart`} caption={data.candles.length ? "OKX 1m candles from PostgreSQL" : `No ${asset.symbol} OHLCV rows in PostgreSQL yet`}>
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
          <TerminalPanel title={`Order Book (OKX / ${okxPair})`}>
            {bidRows.length || askRows.length ? (
              <div className="grid grid-cols-2 gap-3">
                <TerminalTable columns={["Bid", "Size"]} rows={bidRows} />
                <TerminalTable columns={["Ask", "Size"]} rows={askRows} />
              </div>
            ) : (
              <EmptyState label={`Live order book endpoint for ${okxPair} is not connected yet`} />
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
                    <div className="h-full rounded-full bg-emerald-400" style={{ width: `${longLiquidationWidth}%` }} />
                  </div>
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-xs text-slate-500">
                    <span>Shorts</span>
                    <span>{formatCompactCurrency(data.liquidations.shortUsd)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06]">
                    <div className="h-full rounded-full bg-rose-400" style={{ width: `${shortLiquidationWidth}%` }} />
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
