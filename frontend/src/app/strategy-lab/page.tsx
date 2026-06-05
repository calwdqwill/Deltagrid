import { Shell } from "@/components/layout/Shell";
import {
  BarChart,
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

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-white">Strategy Lab</h1>
              <StatusBadge label={live.statusLabel} tone={live.statusTone} />
            </div>
            <div className="mt-1 text-xs text-slate-500">Live inputs are checked; fake backtest results are not shown.</div>
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
            <SelectPill label="Universe" value="BTC / ETH / SOL" />
            <SelectPill label="Price Input" value="Binance OHLCV" />
            <SelectPill label="Funding Input" value="Binance / CoinGlass" />
            <SelectPill label="Execution" value="Disabled" />
          </div>
        </TerminalPanel>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="BTC Price Input" caption="Live candles available for future backtest engine">
            <div className="h-72">
              <LineChart data={live.priceSeries} color="#06B6D4" height={260} />
            </div>
          </TerminalPanel>

          <TerminalPanel title="BTC Funding Input" caption="Live funding history available for future strategy rules">
            <div className="h-72">
              <LineChart data={live.fundingSeries} color="#10B981" height={260} />
            </div>
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_0.85fr]">
          <TerminalPanel title="Readiness Matrix" caption="Input streams required before showing real backtest output">
            <TerminalTable columns={["Input", "Rows", "Status"]} rows={readinessRows} />
          </TerminalPanel>

          <TerminalPanel title="Backtest Output" caption="Blocked until the engine is implemented">
            <BarChart data={[]} colors={["#3B82F6", "#7C3AED", "#EC4899", "#F43F5E"]} />
            <div className="mt-4 rounded-md border border-white/[0.06] bg-white/[0.02] p-4 text-sm leading-6 text-slate-400">
              PnL, drawdown, trade log and Sharpe should only appear after a real backtest engine writes or computes
              results from PostgreSQL inputs.
            </div>
          </TerminalPanel>
        </div>
      </div>
    </Shell>
  );
}
