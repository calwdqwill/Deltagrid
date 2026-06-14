import { Shell } from "@/components/layout/Shell";
import {
  formatCompactCurrency,
  KpiStrip,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveArbitrageScanner } from "@/lib/terminal/live-streams";
import { LiveArbitrageOpportunity } from "@/lib/terminal/live-streams";

export const dynamic = "force-dynamic";

function formatPercent(value: number | null): string {
  if (value === null) return "No data";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(3)}%`;
}

function typeLabel(type: LiveArbitrageOpportunity["type"]): string {
  if (type === "basis") return "Basis";
  return "Funding Bias";
}

function candidateLabel(opportunity: LiveArbitrageOpportunity): string {
  return `${opportunity.asset} ${typeLabel(opportunity.type)}`;
}

function sourceLabel(source: string): string {
  if (source.includes("basis_premium")) return "Basis + funding DB";
  return source;
}

export default async function ArbitrageScannerPage() {
  const live = await getLiveArbitrageScanner();
  const rows = live.opportunities.map((opportunity) => [
    <span key="candidate" className="font-semibold text-white">
      {candidateLabel(opportunity)}
    </span>,
    <span key="type" className="text-slate-300">
      {typeLabel(opportunity.type)}
    </span>,
    <span key="asset" className="font-semibold text-slate-100">
      {opportunity.asset}
    </span>,
    opportunity.longLeg,
    opportunity.shortLeg,
    <span key="edge" className={toneText("positive")}>
      {formatPercent(opportunity.edgePct)}
    </span>,
    <span key="funding" className={toneText(opportunity.fundingPct === null ? "warning" : opportunity.fundingPct >= 0 ? "positive" : "negative")}>
      {formatPercent(opportunity.fundingPct)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {opportunity.openInterestUsd === null ? "No data" : formatCompactCurrency(opportunity.openInterestUsd)}
    </span>,
    sourceLabel(opportunity.source),
    <span key="risk" className={toneText(opportunity.riskNote === "Data-backed" ? "positive" : "warning")}>
      {opportunity.riskNote}
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Arbitrage Scanner</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Live Basis & Funding Scan</h1>
          </div>
          <StatusBadge label={live.statusLabel} tone={live.statusTone} />
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Mode" value="Basis / Funding" />
            <SelectPill label="Assets" value="BTC / ETH / SOL" />
            <SelectPill label="Spot Source" value="CoinGecko" />
            <SelectPill label="Perp Source" value="Binance" />
            <SelectPill label="Risk" value="Read-only research" />
          </div>
        </TerminalPanel>

        <KpiStrip metrics={live.kpis} />

        <TerminalPanel
          title="Opportunity Table"
          caption="Read-only research candidates from persisted basis/funding streams, not execution-grade trade instructions"
        >
          <TerminalTable
            columns={[
              "Candidate",
              "Type",
              "Asset",
              "Long Leg",
              "Short Leg",
              "Basis Edge",
              "Funding",
              "Open Interest",
              "Evidence",
              "Risk Note",
            ]}
            rows={rows}
          />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
