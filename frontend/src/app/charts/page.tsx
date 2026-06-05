import { Shell } from "@/components/layout/Shell";
import {
  BarChart,
  KpiStrip,
  LineChart,
  SegmentedControl,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
} from "@/components/terminal/terminal-ui";
import { getLiveChartsWorkspace, TRACKED_SYMBOLS } from "@/lib/terminal/live-streams";

export const dynamic = "force-dynamic";

function normalizeSymbol(value?: string): string {
  const normalized = value?.toUpperCase();
  return TRACKED_SYMBOLS.includes(normalized as (typeof TRACKED_SYMBOLS)[number]) ? normalized ?? "BTC" : "BTC";
}

export default async function ChartsPage({ searchParams }: { searchParams?: { symbol?: string } }) {
  const symbol = normalizeSymbol(searchParams?.symbol);
  const live = await getLiveChartsWorkspace(symbol);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Charts</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Live Stream Workspace</h1>
          </div>
          <StatusBadge label={live.statusLabel} tone={live.statusTone} />
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Asset" value={live.symbol} />
            <SelectPill label="Exchange" value="Binance" />
            <SelectPill label="Market" value="USD-M Perp" />
            <SelectPill label="Timeframe" value="1m / latest 1000" />
            <SelectPill label="Overlays" value="OI / Basis / Funding / L/S" />
          </div>
          <div className="mt-4">
            <SegmentedControl
              items={TRACKED_SYMBOLS.map((item) => ({ label: item, href: `/charts?symbol=${item}` }))}
              active={live.symbol}
            />
          </div>
        </TerminalPanel>

        <KpiStrip metrics={live.kpis} />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title={`${live.symbol} Price`} caption="Binance 1m close from PostgreSQL">
            <div className="h-[320px]">
              <LineChart data={live.priceSeries} color="#06B6D4" height={300} />
            </div>
          </TerminalPanel>

          <TerminalPanel title="Quote Volume" caption="Binance 1m quote volume">
            <BarChart data={live.volumeSeries.slice(-48)} colors={["#3B82F6", "#06B6D4", "#10B981"]} />
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="Open Interest" caption="CoinGlass snapshot preferred, Binance fallback">
            <div className="h-[280px]">
              <LineChart data={live.openInterestSeries} color="#7C3AED" height={260} />
            </div>
          </TerminalPanel>

          <TerminalPanel title="Basis Premium" caption="CoinGecko spot vs Binance perp approximate snapshot">
            <div className="h-[280px]">
              <LineChart data={live.basisSeries} color="#F59E0B" height={260} />
            </div>
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="Funding Rate" caption="Binance funding history, shown as percent">
            <div className="h-[280px]">
              <LineChart data={live.fundingSeries} color="#10B981" height={260} />
            </div>
          </TerminalPanel>

          <TerminalPanel title="Long Account Ratio" caption="Binance global long/short account ratio">
            <div className="h-[280px]">
              <LineChart data={live.longRatioSeries} color="#EC4899" height={260} />
            </div>
          </TerminalPanel>
        </div>

        <TerminalPanel title="Live Sources" caption="All rows are read from backend data-layer endpoints">
          <TerminalTable columns={["Stream", "Rows", "Source"]} rows={live.sourceRows} />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
