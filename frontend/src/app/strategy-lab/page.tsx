import { Shell } from "@/components/layout/Shell";
import {
  BarChart,
  formatNumber,
  KpiStrip,
  LineChart,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { terminalDataAdapter } from "@/lib/terminal/adapters";

export default async function StrategyLabPage() {
  const data = await terminalDataAdapter.getStrategyLab();

  const parameterRows = data.parameters.map((param) => [
    param.label,
    <span key="value" className="font-mono text-slate-100">
      {param.value}
    </span>,
  ]);

  const tradeRows = data.trades.map((trade) => [
    trade.time,
    trade.asset,
    <span key="side" className={trade.side === "Long" ? "text-blue-300" : "text-rose-300"}>
      {trade.side}
    </span>,
    <span key="entry" className="font-mono">
      {formatNumber(trade.entry)}
    </span>,
    <span key="exit" className="font-mono">
      {formatNumber(trade.exit)}
    </span>,
    <span key="pnl" className={toneText(trade.pnl >= 0 ? "positive" : "negative")}>
      {trade.pnl > 0 ? "+" : ""}
      {trade.pnl.toFixed(2)}%
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-white">{data.name}</h1>
              <StatusBadge label={data.status} tone="positive" />
            </div>
            <div className="mt-1 text-xs text-slate-500">Backtest #1 · mock run result</div>
          </div>
          <div className="flex items-center gap-2">
            <button className="min-h-9 rounded-lg bg-indigo-600 px-4 text-xs font-semibold text-white transition-colors hover:bg-indigo-500" type="button">
              Run Backtest
            </button>
            <button className="min-h-9 rounded-lg border border-white/10 px-3 text-xs font-medium text-slate-300 transition-colors hover:bg-white/[0.06]" type="button">
              Share
            </button>
            <button className="min-h-9 rounded-lg border border-white/10 px-3 text-xs font-medium text-slate-300 transition-colors hover:bg-white/[0.06]" type="button">
              Export
            </button>
          </div>
        </div>

        <KpiStrip metrics={data.metrics} />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <TerminalPanel title="Equity Curve" actions={<div className="flex gap-1 text-[10px] text-slate-500"><span>1D</span><span>1W</span><span>1M</span><span>ALL</span></div>}>
            <div className="h-72">
              <LineChart data={data.equityCurve} color="#F43F5E" height={260} />
            </div>
          </TerminalPanel>

          <TerminalPanel title="Drawdown" actions={<div className="flex gap-1 text-[10px] text-slate-500"><span>1D</span><span>1W</span><span>1M</span><span>ALL</span></div>}>
            <div className="h-72">
              <LineChart data={data.drawdown} color="#F43F5E" height={260} />
            </div>
          </TerminalPanel>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.55fr_0.9fr_1.45fr]">
          <TerminalPanel title="Parameters">
            <div className="mb-3 grid grid-cols-1 gap-2">
              <SelectPill label="Strategy" value="Mean Reversion" />
              <SelectPill label="Universe" value="BTC / ETH / SOL" />
            </div>
            <TerminalTable columns={["Parameter", "Value"]} rows={parameterRows} />
          </TerminalPanel>

          <TerminalPanel title="PnL Distribution">
            <BarChart data={data.pnlDistribution} colors={["#3B82F6", "#7C3AED", "#EC4899", "#F43F5E"]} />
          </TerminalPanel>

          <TerminalPanel title="Trade Log (Last 10)">
            <TerminalTable columns={["Time", "Asset", "Side", "Entry", "Exit", "PnL"]} rows={tradeRows} />
          </TerminalPanel>
        </div>
      </div>
    </Shell>
  );
}
