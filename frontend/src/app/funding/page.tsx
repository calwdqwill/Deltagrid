import { Shell } from "@/components/layout/Shell";
import {
  formatSigned,
  KpiStrip,
  LineChart,
  SegmentedControl,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { terminalDataAdapter } from "@/lib/terminal/adapters";

export default async function FundingPage() {
  const data = await terminalDataAdapter.getFundingOverview();

  const fundingSeries = data.history.map((point, index) => ({ label: String(index), value: point.rate }));
  const arbitrageRows = data.arbitrage.map((item) => [
    <span key="asset" className="font-semibold text-cyan-200">
      {item.asset}
    </span>,
    item.longLeg,
    item.shortLeg,
    <span key="edge" className="font-mono text-emerald-300">
      {formatSigned(item.fundingEdge)}
    </span>,
    <span key="apr" className="font-mono text-slate-100">
      {item.netApr.toFixed(1)}%
    </span>,
    <span key="liq" className="font-mono">
      {item.liquidityScore}
    </span>,
    <span key="risk" className="font-mono text-amber-300">
      {item.riskScore}
    </span>,
  ]);

  const legsRows = data.longShortLegs.map((leg) => [
    leg.asset,
    leg.venue,
    <span key="receive" className={leg.receiveSide === "short" ? "text-rose-300" : "text-emerald-300"}>
      {leg.receiveSide === "short" ? "Short perp receives" : "Long perp receives"}
    </span>,
    <span key="rate" className={toneText(leg.currentRate >= 0 ? "positive" : "negative")}>
      {formatSigned(leg.currentRate)}
    </span>,
    <span key="apr" className="font-mono text-slate-100">
      {leg.estimatedApr.toFixed(1)}%
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Funding</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Overview</h1>
          </div>
          <div className="flex items-center gap-2">
            <SegmentedControl
              items={["Overview", "History", "Perp DEX", "Arbitrage", "Matrix", "Predicted", "Legs"]}
              active="Overview"
            />
            <StatusBadge label="Funding first-class module" tone="positive" />
          </div>
        </div>

        <KpiStrip metrics={data.kpis} />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <TerminalPanel title="Funding Matrix (8h)" caption="Rows are assets, columns are venues">
            <div className="overflow-x-auto">
              <table className="w-full border-separate border-spacing-0 text-xs">
                <thead>
                  <tr>
                    <th className="border-b border-white/[0.08] bg-white/[0.03] px-3 py-2 text-left text-slate-500">
                      Asset
                    </th>
                    {data.venues.map((venue) => (
                      <th key={venue} className="border-b border-white/[0.08] bg-white/[0.03] px-3 py-2 text-left text-amber-200">
                        {venue}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.matrix.map((row) => (
                    <tr key={row[0].asset}>
                      <td className="border-b border-white/[0.06] px-3 py-2.5 font-semibold text-slate-100">
                        {row[0].asset}
                      </td>
                      {row.map((cell) => {
                        const positive = cell.rate >= 0;
                        return (
                          <td
                            key={`${cell.asset}-${cell.venue}`}
                            className={`border-b border-white/[0.06] px-3 py-2.5 font-mono ${
                              positive ? "bg-emerald-500/16 text-emerald-200" : "bg-rose-500/18 text-rose-200"
                            }`}
                          >
                            {formatSigned(cell.rate)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TerminalPanel>

          <TerminalPanel title="Funding History" caption="BTC · Hyperliquid">
            <div className="h-[310px]">
              <LineChart data={fundingSeries} color="#10B981" height={280} />
            </div>
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_0.72fr]">
          <TerminalPanel
            title="Funding Arbitrage Opportunities"
            caption="Funding edge minus fees, slippage, borrow/hedge cost and venue risk"
          >
            <TerminalTable
              columns={["Asset", "Long Leg", "Short Leg", "Funding Edge", "Net APR", "Liquidity", "Risk"]}
              rows={arbitrageRows}
            />
          </TerminalPanel>

          <TerminalPanel title="Long / Short Legs" caption="Where funding is received and hedged">
            <TerminalTable columns={["Asset", "Venue", "Receive", "Rate", "Est APR"]} rows={legsRows} />
          </TerminalPanel>
        </div>

        <TerminalPanel title="Predicted Funding (Next 8h)">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
            {data.predicted.map((point) => (
              <div key={point.asset} className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
                <div className="text-xs text-slate-500">{point.asset}</div>
                <div className="mt-2 font-mono text-lg text-slate-100">{formatSigned(point.predicted ?? point.rate)}</div>
                <div className={toneText((point.predicted ?? point.rate) >= point.rate ? "positive" : "negative")}>
                  {point.predicted && point.predicted >= point.rate ? "Up" : "Down"}
                </div>
              </div>
            ))}
          </div>
        </TerminalPanel>
      </div>
    </Shell>
  );
}
