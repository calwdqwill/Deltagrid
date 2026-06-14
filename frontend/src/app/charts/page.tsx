import { Shell } from "@/components/layout/Shell";
import { InteractiveCandlestickChart } from "@/components/terminal/InteractiveCandlestickChart";
import {
  BarChart,
  formatCompactCurrency,
  formatSigned,
  KpiStrip,
  LineChart,
  SegmentedControl,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
} from "@/components/terminal/terminal-ui";
import {
  CHART_INTERVALS,
  CHART_RANGES,
  ChartInterval,
  ChartRange,
  getLiveChartsWorkspace,
  TRACKED_SYMBOLS,
} from "@/lib/terminal/live-streams";

export const dynamic = "force-dynamic";

function normalizeSymbol(value?: string): string {
  const normalized = value?.toUpperCase();
  return TRACKED_SYMBOLS.includes(normalized as (typeof TRACKED_SYMBOLS)[number]) ? normalized ?? "BTC" : "BTC";
}

function normalizeInterval(value?: string): ChartInterval {
  return CHART_INTERVALS.includes(value as ChartInterval) ? (value as ChartInterval) : "1m";
}

function normalizeRange(value?: string): ChartRange {
  return CHART_RANGES.includes(value as ChartRange) ? (value as ChartRange) : "24h";
}

function chartHref(symbol: string, interval: ChartInterval, range: ChartRange): string {
  return `/charts?symbol=${symbol}&interval=${interval}&range=${range}`;
}

function chartTooltip(label: string, formatter: (value: number) => string) {
  return (point: { label: string; value: number }) => `${label} ${point.label}: ${formatter(point.value)}`;
}

export default async function ChartsPage({ searchParams }: { searchParams?: { symbol?: string; interval?: string; range?: string } }) {
  const symbol = normalizeSymbol(searchParams?.symbol);
  const interval = normalizeInterval(searchParams?.interval);
  const range = normalizeRange(searchParams?.range);
  const live = await getLiveChartsWorkspace(symbol, interval, range);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Charts</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Interactive Price Workspace</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge label={live.statusLabel} tone={live.statusTone} />
            <StatusBadge label={live.freshnessLabel} tone={live.freshnessTone} />
          </div>
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Asset" value={live.symbol} />
            <SelectPill label="Exchange" value={live.exchangeLabel} />
            <SelectPill label="Market" value="USDT Swap" />
            <SelectPill label="Interval" value={live.interval} />
            <SelectPill label="Range" value={live.rangeLabel} />
          </div>
          <div className="mt-4 space-y-3">
            <SegmentedControl
              items={TRACKED_SYMBOLS.map((item) => ({ label: item, href: chartHref(item, live.interval, live.range) }))}
              active={live.symbol}
            />
            <SegmentedControl
              items={CHART_INTERVALS.map((item) => ({ label: item, href: chartHref(live.symbol, item, live.range) }))}
              active={live.interval}
            />
            <SegmentedControl
              items={CHART_RANGES.map((item) => ({ label: item, href: chartHref(live.symbol, live.interval, item) }))}
              active={live.range}
            />
          </div>
        </TerminalPanel>

        <KpiStrip metrics={live.kpis} />

        <TerminalPanel
          title={`${live.symbol} ${live.interval} Candles`}
          caption={`${live.exchangeLabel} USDT Swap - ${live.rangeLabel} - latest ${live.latestCandleIso}`}
        >
          <InteractiveCandlestickChart candles={live.candles} />
        </TerminalPanel>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="Open Interest" caption={`${live.exchangeLabel} snapshot preferred, CoinGlass fallback`}>
            <div className="h-[280px]">
              <LineChart
                data={live.openInterestSeries}
                color="#7C3AED"
                height={260}
                valueFormatter={formatCompactCurrency}
                tooltipFormatter={chartTooltip("Open interest", formatCompactCurrency)}
              />
            </div>
          </TerminalPanel>

          <TerminalPanel title="Basis Premium" caption={`CoinGecko spot vs ${live.exchangeLabel} perp approximate snapshot`}>
            <div className="h-[280px]">
              <LineChart
                data={live.basisSeries}
                color="#F59E0B"
                height={260}
                valueFormatter={(value) => formatSigned(value)}
                tooltipFormatter={chartTooltip("Basis", (value) => formatSigned(value))}
              />
            </div>
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="Funding Rate" caption={`${live.exchangeLabel} funding history, shown as percent`}>
            <div className="h-[280px]">
              <LineChart
                data={live.fundingSeries}
                color="#10B981"
                height={260}
                valueFormatter={(value) => formatSigned(value)}
                tooltipFormatter={chartTooltip("Funding", (value) => formatSigned(value))}
              />
            </div>
          </TerminalPanel>

          <TerminalPanel title="Long Account Ratio" caption={`${live.exchangeLabel} long/short account ratio`}>
            <div className="h-[280px]">
              <LineChart
                data={live.longRatioSeries}
                color="#EC4899"
                height={260}
                valueFormatter={(value) => formatSigned(value)}
                tooltipFormatter={chartTooltip("Long account ratio", (value) => formatSigned(value))}
              />
            </div>
          </TerminalPanel>
        </div>

        <TerminalPanel title="Quote Volume" caption={`${live.exchangeLabel} ${live.interval} quote volume`}>
          <BarChart data={live.volumeSeries.slice(-120)} colors={["#3B82F6", "#06B6D4", "#10B981"]} valueFormatter={formatCompactCurrency} />
        </TerminalPanel>

        <TerminalPanel title="Live Sources" caption="All rows are read from backend data-layer endpoints">
          <TerminalTable columns={["Stream", "Rows", "Source"]} rows={live.sourceRows} />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
