import { Shell } from "@/components/layout/Shell";
import {
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { terminalDataAdapter } from "@/lib/terminal/adapters";

export default async function ArbitrageScannerPage() {
  const data = await terminalDataAdapter.getArbitrageScanner();
  const rows = data.opportunities.map((opportunity) => [
    <span key="id" className="font-mono text-slate-500">
      {opportunity.id}
    </span>,
    opportunity.type.replaceAll("_", " "),
    <span key="asset" className="font-semibold text-slate-100">
      {opportunity.asset}
    </span>,
    opportunity.longLeg,
    opportunity.shortLeg,
    <span key="edge" className={toneText("positive")}>
      {opportunity.edge.toFixed(2)}%
    </span>,
    <span key="return" className="font-mono text-slate-100">
      {opportunity.expectedReturn.toFixed(1)}%
    </span>,
    opportunity.liquidity,
    <span key="fees" className="font-mono">
      {opportunity.fees.toFixed(2)}%
    </span>,
    <span key="slippage" className="font-mono">
      {opportunity.slippage.toFixed(2)}%
    </span>,
    <span key="risk" className="font-mono text-amber-300">
      {opportunity.riskScore}
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Arbitrage Scanner</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Non-Funding Opportunities</h1>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge label="Basis, spread, liquidity and OI only" tone="neutral" />
          </div>
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Mode" value="Basis / Spread" />
            <SelectPill label="Assets" value="Top 25" />
            <SelectPill label="Venues" value="CEX + Perp DEX" />
            <SelectPill label="Min Edge" value="0.10%" />
            <SelectPill label="Risk Cap" value="Medium" />
          </div>
        </TerminalPanel>

        <TerminalPanel title="Opportunity Table" caption="Basis, cross-exchange spread, liquidity anomaly and OI divergence">
          <TerminalTable
            columns={[
              "Opportunity",
              "Type",
              "Asset",
              "Long Leg",
              "Short Leg",
              "Edge",
              "Expected Return",
              "Liquidity",
              "Fees",
              "Slippage",
              "Risk",
            ]}
            rows={rows}
          />
        </TerminalPanel>
      </div>
    </Shell>
  );
}
