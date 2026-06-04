import { Shell } from "@/components/layout/Shell";
import {
  DonutChart,
  formatCompactCurrency,
  formatNumber,
  KpiStrip,
  LineChart,
  LinkButton,
  SegmentedControl,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
} from "@/components/terminal/terminal-ui";
import { terminalDataAdapter } from "@/lib/terminal/adapters";

export default async function PerpDexPage() {
  const data = await terminalDataAdapter.getPerpDexOverview();
  const volumeSeries = data.stackedVolume.map((point) => ({
    label: point.time,
    value: Object.values(point.values).reduce((sum, value) => sum + value, 0),
  }));

  const marketRows = data.markets.map((market) => [
    <span key="market" className="font-medium text-slate-100">
      {market.market}
    </span>,
    market.venue,
    <span key="price" className="font-mono">
      ${formatNumber(market.price)}
    </span>,
    <span key="volume" className="font-mono">
      {formatCompactCurrency(market.volume24h)}
    </span>,
    <span key="oi" className="font-mono">
      {formatCompactCurrency(market.openInterest)}
    </span>,
    <span key="liq" className="font-mono text-emerald-300">
      {market.liquidityScore}/100
    </span>,
    <span key="ratio" className="font-mono">
      {market.oiToVolume.toFixed(2)}
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Perp DEX</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Intelligence Overview</h1>
          </div>
          <div className="flex items-center gap-2">
            <SegmentedControl items={["Overview", "Venues", "Open Interest", "Liquidity", "Opportunities"]} active="Overview" />
            <StatusBadge label="Funding moved to Funding module" tone="neutral" />
          </div>
        </div>

        <KpiStrip metrics={data.kpis} />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="Perp DEX Volume Share (24h)">
            <DonutChart
              data={data.volumeShare}
              center={
                <div>
                  <div className="font-mono text-lg font-semibold text-white">$42.6B</div>
                  <div className="text-xs text-slate-500">Total</div>
                </div>
              }
            />
          </TerminalPanel>

          <TerminalPanel title="Open Interest Share">
            <DonutChart
              data={data.oiShare}
              center={
                <div>
                  <div className="font-mono text-lg font-semibold text-white">$18.7B</div>
                  <div className="text-xs text-slate-500">Total</div>
                </div>
              }
            />
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.4fr_0.6fr]">
          <TerminalPanel title="Perp DEX Volume (24h)" caption="Aggregated venue activity">
            <div className="h-72">
              <LineChart data={volumeSeries} color="#3B82F6" height={260} />
            </div>
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
              {data.volumeShare.slice(0, 5).map((venue, index) => (
                <span key={venue.label} className="inline-flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: ["#3B82F6", "#7C3AED", "#06B6D4", "#10B981", "#EC4899"][index] }}
                  />
                  {venue.label}
                </span>
              ))}
            </div>
          </TerminalPanel>

          <TerminalPanel title="Liquidity Metrics" caption="Average execution quality">
            <div className="space-y-4">
              {data.liquidityMetrics.map((metric) => (
                <div key={metric.venue}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="text-slate-300">{metric.venue}</span>
                    <span className="font-mono text-slate-400">{metric.score}/100</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400"
                      style={{ width: `${metric.score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-lg border border-white/10 bg-white/[0.035] p-3">
              <div className="text-sm font-medium text-slate-100">Perp DEX Funding</div>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Full funding analytics are handled in the Funding workspace.
              </p>
              <div className="mt-3">
                <LinkButton href="/funding">View Funding</LinkButton>
              </div>
            </div>
          </TerminalPanel>
        </div>

        <TerminalPanel title="Top Perp Markets" caption="No full funding dashboard on this screen">
          <TerminalTable
            columns={["Market", "Venue", "Price", "24h Volume", "Open Interest", "Liquidity", "OI / Volume"]}
            rows={marketRows}
          />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
