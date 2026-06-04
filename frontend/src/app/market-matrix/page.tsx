import { Shell } from "@/components/layout/Shell";
import {
  formatNumber,
  SegmentedControl,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  toneText,
} from "@/components/terminal/terminal-ui";
import { terminalDataAdapter } from "@/lib/terminal/adapters";

function cellTone(value: number, average: number) {
  const diff = (value - average) / average;
  if (diff > 0.002) return "bg-emerald-500/18 text-emerald-100";
  if (diff < -0.002) return "bg-rose-500/18 text-rose-100";
  return "bg-slate-500/10 text-slate-200";
}

export default async function MarketMatrixPage() {
  const data = await terminalDataAdapter.getMarketMatrix();

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Market Matrix</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Overview (No Funding)</h1>
          </div>
          <StatusBadge label="Price / spread / OI matrix only" tone="neutral" />
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Metric" value="Price" />
            <SelectPill label="Market Type" value="Perpetuals" />
            <SelectPill label="Assets" value="Top 10" />
            <SelectPill label="Venues" value="6 selected" />
            <SelectPill label="Timeframe" value="1D" />
          </div>
          <div className="mt-4">
            <SegmentedControl
              items={["Price", "Spread", "Open Interest", "Volume", "Liquidity", "Depth", "Slippage"]}
              active="Price"
            />
          </div>
        </TerminalPanel>

        <TerminalPanel title="Cross-Exchange Price Matrix" caption="Rows are assets, columns are venues">
          <div className="overflow-x-auto rounded-lg border border-white/[0.08]">
            <table className="w-full border-separate border-spacing-0 text-sm">
              <thead>
                <tr>
                  <th className="sticky left-0 z-10 border-b border-white/[0.08] bg-[#101827] px-4 py-3 text-left text-slate-500">
                    Asset
                  </th>
                  {data.venues.map((venue) => (
                    <th key={venue} className="border-b border-white/[0.08] bg-[#101827] px-4 py-3 text-left text-slate-300">
                      {venue}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row) => {
                  const values = Object.values(row.values);
                  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
                  return (
                    <tr key={row.asset}>
                      <td className="sticky left-0 z-10 border-b border-white/[0.06] bg-[#101827] px-4 py-3 font-semibold text-white">
                        {row.asset}
                      </td>
                      {data.venues.map((venue) => (
                        <td
                          key={`${row.asset}-${venue}`}
                          className={`border-b border-white/[0.06] px-4 py-3 font-mono ${cellTone(row.values[venue], average)}`}
                        >
                          {row.values[venue] > 100 ? formatNumber(row.values[venue]) : row.values[venue].toFixed(3)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </TerminalPanel>

        <TerminalPanel title="Matrix Insights">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
            {data.insights.map((insight) => (
              <div key={insight.label} className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
                <div className="text-xs text-slate-500">{insight.label}</div>
                <div className={`mt-3 text-base font-semibold ${toneText(insight.tone)}`}>{insight.value}</div>
                <div className="mt-2 font-mono text-sm text-slate-300">{insight.caption}</div>
              </div>
            ))}
          </div>
        </TerminalPanel>
      </div>
    </Shell>
  );
}
