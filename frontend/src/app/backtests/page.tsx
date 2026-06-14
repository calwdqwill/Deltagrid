import { Shell } from "@/components/layout/Shell";
import { LinkButton, StatusBadge, TerminalPanel } from "@/components/terminal/terminal-ui";

export default function BacktestsPage() {
  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Backtests</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Backtest History</h1>
          </div>
          <StatusBadge label="Engine pending" tone="warning" />
        </div>

        <TerminalPanel title="Run History" caption="Real backtest runs will appear here after the engine is connected">
          <div className="rounded-md border border-white/[0.06] bg-white/[0.02] p-4 text-sm leading-6 text-slate-400">
            Historical PnL, drawdown, trade logs and Sharpe stay hidden until the production backtest engine computes
            results from PostgreSQL market data.
          </div>
          <div className="mt-4">
            <LinkButton href="/strategy-lab">Open Strategy Lab</LinkButton>
          </div>
        </TerminalPanel>
      </div>
    </Shell>
  );
}
