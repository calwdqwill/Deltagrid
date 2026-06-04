import { Shell } from "@/components/layout/Shell";
import {
  LineChart,
  SegmentedControl,
  SelectPill,
  StatusBadge,
  TerminalPanel,
} from "@/components/terminal/terminal-ui";

const previewSeries = [
  152, 151, 153, 155, 154, 158, 162, 166, 164, 161, 158, 156, 157, 159, 158, 160, 162, 161,
].map((value, index) => ({ label: String(index), value }));

export default function ChartsPage() {
  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Charts</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Chart Workspace Placeholder</h1>
          </div>
          <StatusBadge label="Lightweight Charts planned" tone="warning" />
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Asset" value="SOL" />
            <SelectPill label="Exchange" value="Binance" />
            <SelectPill label="Market" value="Perp" />
            <SelectPill label="Timeframe" value="1H" />
            <SelectPill label="Overlay" value="Volume / OI / Basis" />
          </div>
          <div className="mt-4">
            <SegmentedControl items={["Price Chart", "Volume Chart", "OI Chart", "Basis Chart", "Funding Chart"]} active="Price Chart" />
          </div>
        </TerminalPanel>

        <TerminalPanel
          title="Price Chart Preview"
          caption="This placeholder keeps the MVP navigation complete without adding charting dependencies in this iteration"
        >
          <div className="h-[460px]">
            <LineChart data={previewSeries} color="#06B6D4" height={420} />
          </div>
          <div className="mt-4 rounded-lg border border-amber-300/20 bg-amber-300/[0.08] p-4 text-sm leading-6 text-amber-100">
            Full charting should use TradingView Lightweight Charts, not TradingView Advanced Charts or paid charting
            solutions. The implementation task is tracked in `BACKLOG.md`.
          </div>
        </TerminalPanel>
      </div>
    </Shell>
  );
}
