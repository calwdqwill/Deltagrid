import { Shell } from "@/components/layout/Shell";
import {
  formatNumber,
  formatSigned,
  KpiStrip,
  LineChart,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveStrategyReadiness } from "@/lib/terminal/live-streams";

export const dynamic = "force-dynamic";

function formatPriceAxis(value: number): string {
  return value >= 100 ? `$${formatNumber(value)}` : `$${value.toFixed(4)}`;
}

export default async function StrategyLabPage() {
  const live = await getLiveStrategyReadiness();
  const readinessRows = live.readinessRows.map(([input, rows, status]) => [
    input,
    <span key="rows" className="font-mono text-slate-100">
      {rows}
    </span>,
    <span key="status" className={toneText(status === "Ready" ? "positive" : "warning")}>
      {status}
    </span>,
  ]);
  const outputRows = [
    ["PnL / Equity Curve", "Pending engine", "Only real computed results from PostgreSQL inputs"],
    ["Drawdown / Sharpe", "Pending engine", "Real performance metrics only"],
    ["Trade Log", "Pending engine", "Requires deterministic strategy execution"],
    ["Execution", "Disabled", "Research-only demo state"],
  ].map(([output, status, rule]) => [
    output,
    <span key="status" className={toneText(status === "Disabled" ? "warning" : "neutral")}>
      {status}
    </span>,
    rule,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-white">Strategy Lab</h1>
              <StatusBadge label={live.statusLabel} tone={live.statusTone} />
            </div>
            <div className="mt-1 text-xs text-slate-500">Live inputs are checked; synthetic backtest results are hidden.</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="min-h-9 cursor-not-allowed rounded-lg border border-amber-300/25 bg-amber-300/10 px-4 text-xs font-semibold text-amber-100"
              type="button"
              disabled
            >
              Backtest Engine Pending
            </button>
          </div>
        </div>

        <KpiStrip metrics={live.kpis} />

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Strategy" value="Basis / Funding Research" />
            <SelectPill label="Universe" value="BTC input demo" />
            <SelectPill label="Price Input" value="OKX OHLCV" />
            <SelectPill label="Funding Input" value="OKX / CoinGlass" />
            <SelectPill label="Output Policy" value="Real PnL only" />
          </div>
        </TerminalPanel>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="BTC Price Input" caption="Live candles available for future backtest engine">
            <div className="h-72">
              <LineChart
                data={live.priceSeries}
                color="#06B6D4"
                height={260}
                valueFormatter={formatPriceAxis}
                tooltipFormatter={(point) => `BTC price ${point.label}: ${formatPriceAxis(point.value)}`}
              />
            </div>
          </TerminalPanel>

          <TerminalPanel title="BTC Funding Input" caption="Live funding history available for future strategy rules">
            <div className="h-72">
              <LineChart
                data={live.fundingSeries}
                color="#10B981"
                height={260}
                valueFormatter={(value) => formatSigned(value)}
                tooltipFormatter={(point) => `BTC funding ${point.label}: ${formatSigned(point.value)}`}
              />
            </div>
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_0.85fr]">
          <TerminalPanel title="Readiness Matrix" caption="Input streams required before showing real backtest output">
            <TerminalTable columns={["Input", "Rows", "Status"]} rows={readinessRows} />
          </TerminalPanel>

          <TerminalPanel title="Backtest Output Boundary" caption="Blocked until the real engine is implemented">
            <TerminalTable columns={["Output", "Status", "Rule"]} rows={outputRows} />
            <div className="mt-4 rounded-md border border-white/[0.06] bg-white/[0.02] p-4 text-sm leading-6 text-slate-400">
              Live inputs are ready for research. PnL, drawdown, trade log and Sharpe stay hidden until a real
              backtest engine computes them from PostgreSQL inputs.
            </div>
          </TerminalPanel>
        </div>
      </div>
    </Shell>
  );
}
