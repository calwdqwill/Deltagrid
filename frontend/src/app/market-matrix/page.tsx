import { Shell } from "@/components/layout/Shell";
import {
  formatCompactCurrency,
  formatNumber,
  KpiStrip,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { CORE_SYMBOLS_LABEL, getLiveMarketMatrix, LiveMatrixRow } from "@/lib/terminal/live-streams";

export const dynamic = "force-dynamic";

function formatMaybePrice(value: number | null): string {
  if (value === null) return "No data";
  return value >= 100 ? `$${formatNumber(value)}` : `$${value.toFixed(4)}`;
}

function formatMaybePercent(value: number | null, digits = 3): string {
  if (value === null) return "No data";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

function percentTone(value: number | null) {
  if (value === null) return "warning";
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function rowCoverage(row: LiveMatrixRow): { label: string; tone: "positive" | "warning" | "negative" } {
  const fields = [row.spotPrice, row.perpPrice, row.basisPct, row.fundingPct, row.openInterestUsd, row.longAccountRatio];
  const liveFields = fields.filter((value) => value !== null).length;

  if (liveFields >= 5) return { label: "Live", tone: "positive" };
  if (liveFields >= 2) return { label: "Partial", tone: "warning" };
  return { label: "Missing", tone: "negative" };
}

function rowCells(row: LiveMatrixRow) {
  const coverage = rowCoverage(row);

  return [
    <span key="asset" className="font-semibold text-white">
      {row.asset}
    </span>,
    <span key="spot" className="font-mono text-slate-100">
      {formatMaybePrice(row.spotPrice)}
    </span>,
    <span key="perp" className="font-mono text-slate-100">
      {formatMaybePrice(row.perpPrice)}
    </span>,
    <span key="basis" className={toneText(percentTone(row.basisPct))}>
      {formatMaybePercent(row.basisPct)}
    </span>,
    <span key="funding" className={toneText(percentTone(row.fundingPct))}>
      {formatMaybePercent(row.fundingPct)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {row.openInterestUsd === null ? "No data" : formatCompactCurrency(row.openInterestUsd)}
    </span>,
    <span key="long" className={toneText(row.longAccountRatio === null ? "warning" : row.longAccountRatio >= 50 ? "positive" : "negative")}>
      {formatMaybePercent(row.longAccountRatio, 2)}
    </span>,
    <span key="coverage" className={toneText(coverage.tone)}>
      {coverage.label}
    </span>,
  ];
}

export default async function MarketMatrixPage() {
  const live = await getLiveMarketMatrix();
  const sourceRows = live.sourceRows.map(([stream, source]) => [
    stream,
    source,
    <span key="status" className={toneText("positive")}>
      Connected
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Market Matrix</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Live Data Matrix</h1>
          </div>
          <StatusBadge label={live.statusLabel} tone={live.statusTone} />
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Universe" value={CORE_SYMBOLS_LABEL} />
            <SelectPill label="Price" value="CoinGecko + OKX" />
            <SelectPill label="Derivatives" value="Funding / OI / L/S" />
            <SelectPill label="Basis" value="Spot vs Perp" />
            <SelectPill label="Coverage" value={`${live.rows.filter((row) => rowCoverage(row).label === "Live").length}/${live.rows.length} live`} />
          </div>
        </TerminalPanel>

        <KpiStrip metrics={live.kpis} />

        <TerminalPanel title="Live Stream Matrix" caption="Rows are assets, columns are persisted data streams">
          <TerminalTable
            columns={["Asset", "Spot", "Perp Close", "Basis", "Funding", "Open Interest", "Long Accounts", "Coverage"]}
            rows={live.rows.map(rowCells)}
          />
        </TerminalPanel>

        <TerminalPanel title="Matrix Sources">
          <TerminalTable columns={["Stream", "Source", "Status"]} rows={sourceRows} />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
