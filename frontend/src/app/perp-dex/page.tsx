import { Shell } from "@/components/layout/Shell";
import {
  formatCompactCurrency,
  formatNumber,
  KpiStrip,
  LinkButton,
  SegmentedControl,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveDataHealth } from "@/lib/terminal/live-data";
import {
  getLiveArbitrageScanner,
  getLiveMarketMatrix,
  LiveArbitrageOpportunity,
  LiveMatrixRow,
  TRACKED_SYMBOLS_LABEL,
} from "@/lib/terminal/live-streams";
import { KpiMetric } from "@/types/terminal";

export const dynamic = "force-dynamic";

const perpDexViews = [
  { view: "overview", label: "Overview", title: "Intelligence Overview", href: "/perp-dex" },
  { view: "venues", label: "Venues", title: "Venues", href: "/perp-dex?view=venues" },
  { view: "open-interest", label: "Open Interest", title: "Open Interest", href: "/perp-dex?view=open-interest" },
  { view: "liquidity", label: "Liquidity", title: "Liquidity", href: "/perp-dex?view=liquidity" },
  { view: "opportunities", label: "Opportunities", title: "Opportunities", href: "/perp-dex?view=opportunities" },
] as const;

type PerpDexView = (typeof perpDexViews)[number]["view"];

function normalizeView(value?: string): PerpDexView {
  return perpDexViews.some((item) => item.view === value) ? (value as PerpDexView) : "overview";
}

function formatRows(value?: number): string {
  return (value ?? 0).toLocaleString("en-US");
}

function formatSyncTime(value: unknown): string {
  if (typeof value !== "string") return "No sync";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No sync";
  return date.toLocaleString("en-US", { dateStyle: "short", timeStyle: "short" });
}

function lastSyncTime(lastSync: Record<string, unknown> | null): string {
  return formatSyncTime(lastSync?.last_sync_at);
}

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

function readinessTone(row: LiveMatrixRow) {
  const readyFields = [row.perpPrice, row.fundingPct, row.openInterestUsd, row.longAccountRatio].filter(
    (value) => value !== null
  ).length;

  if (readyFields >= 3) return "positive";
  if (readyFields >= 1) return "warning";
  return "negative";
}

function readinessLabel(row: LiveMatrixRow): string {
  const tone = readinessTone(row);
  if (tone === "positive") return "Ready";
  if (tone === "warning") return "Partial";
  return "Missing";
}

function perpUniverseCells(row: LiveMatrixRow) {
  const statusTone = readinessTone(row);

  return [
    <span key="asset" className="font-semibold text-white">
      {row.asset}
    </span>,
    <span key="perp" className="font-mono text-slate-100">
      {formatMaybePrice(row.perpPrice)}
    </span>,
    <span key="funding" className={toneText(percentTone(row.fundingPct))}>
      {formatMaybePercent(row.fundingPct)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {row.openInterestUsd === null ? "No data" : formatCompactCurrency(row.openInterestUsd)}
    </span>,
    <span key="basis" className={toneText(percentTone(row.basisPct))}>
      {formatMaybePercent(row.basisPct)}
    </span>,
    <span key="long" className={toneText(row.longAccountRatio === null ? "warning" : row.longAccountRatio >= 50 ? "positive" : "negative")}>
      {formatMaybePercent(row.longAccountRatio, 2)}
    </span>,
    <span key="status" className={toneText(statusTone)}>
      {readinessLabel(row)}
    </span>,
  ];
}

function opportunityCells(opportunity: LiveArbitrageOpportunity) {
  return [
    <span key="asset" className="font-semibold text-white">
      {opportunity.asset}
    </span>,
    opportunity.type.replaceAll("_", " "),
    opportunity.longLeg,
    opportunity.shortLeg,
    <span key="edge" className={toneText("positive")}>
      {formatMaybePercent(opportunity.edgePct)}
    </span>,
    <span key="funding" className={toneText(percentTone(opportunity.fundingPct))}>
      {formatMaybePercent(opportunity.fundingPct)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {opportunity.openInterestUsd === null ? "No data" : formatCompactCurrency(opportunity.openInterestUsd)}
    </span>,
    <span key="risk" className={toneText(opportunity.riskNote === "Data-backed" ? "positive" : "warning")}>
      {opportunity.riskNote}
    </span>,
  ];
}

type PerpDexPageProps = {
  searchParams?: Promise<{ view?: string }>;
};

export default async function PerpDexPage({ searchParams }: PerpDexPageProps) {
  const params = await searchParams;
  const activeView = normalizeView(params?.view);
  const activeTab = perpDexViews.find((item) => item.view === activeView) ?? perpDexViews[0];
  const [health, matrix, scanner] = await Promise.all([
    getLiveDataHealth(),
    getLiveMarketMatrix(),
    getLiveArbitrageScanner(),
  ]);
  const rowCounts = health?.row_counts ?? {};
  const providers = Object.values(health?.providers ?? {});
  const healthyProviders = providers.filter((provider) => provider.healthy).length;
  const livePerpRows = matrix.rows.filter(
    (row) => row.perpPrice !== null || row.fundingPct !== null || row.openInterestUsd !== null
  ).length;
  const largestOi = matrix.rows.reduce<LiveMatrixRow | null>((best, row) => {
    if (row.openInterestUsd === null) return best;
    if (!best || row.openInterestUsd > (best.openInterestUsd ?? 0)) return row;
    return best;
  }, null);
  const largestEdge = scanner.opportunities[0] ?? null;

  const kpis: KpiMetric[] = [
    {
      label: "Perp Inputs",
      value: `${livePerpRows}/${matrix.rows.length}`,
      caption: `${TRACKED_SYMBOLS_LABEL} live streams`,
      tone: livePerpRows === matrix.rows.length ? "positive" : "warning",
    },
    {
      label: "DEX Venue Data",
      value: "Pending",
      caption: "Direct Hyperliquid/dYdX/GMX adapters",
      tone: "warning",
    },
    {
      label: "Largest OI",
      value: largestOi ? largestOi.asset : "No data",
      caption: largestOi ? formatCompactCurrency(largestOi.openInterestUsd ?? 0) : "Open interest",
      tone: largestOi ? "positive" : "warning",
    },
    {
      label: "Funding Rows",
      value: formatRows(rowCounts.funding_rates),
      caption: "OKX/CoinGlass",
      tone: (rowCounts.funding_rates ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Liquidation Rows",
      value: formatRows(rowCounts.liquidations),
      caption: "CoinGlass aggregated",
      tone: (rowCounts.liquidations ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Largest Edge",
      value: largestEdge ? `${largestEdge.asset} ${formatMaybePercent(largestEdge.edgePct)}` : "No data",
      caption: "Basis/funding candidate",
      tone: largestEdge ? "positive" : "warning",
    },
  ];

  const providerRows = providers.map((provider) => [
    provider.provider_name,
    <span key="status" className={toneText(provider.healthy ? "positive" : "warning")}>
      {provider.status}
    </span>,
    lastSyncTime(provider.last_sync),
    provider.last_error_message ?? "-",
  ]);

  const dataCoverageRows = [
    ["OHLCV", rowCounts.ohlcv, "OKX 1m candles"],
    ["Funding", rowCounts.funding_rates, "OKX + CoinGlass"],
    ["Open Interest", rowCounts.open_interest, "OKX preferred, CoinGlass fallback"],
    ["Liquidations", rowCounts.liquidations, "CoinGlass aggregated history"],
    ["Long/Short", rowCounts.long_short_ratio, "OKX account ratio"],
    ["Basis", rowCounts.basis_premium, "CoinGecko spot + OKX perp"],
  ].map(([stream, count, source]) => [
    stream,
    <span key="rows" className="font-mono text-slate-100">
      {formatRows(typeof count === "number" ? count : 0)}
    </span>,
    source,
    <span key="status" className={toneText(typeof count === "number" && count > 0 ? "positive" : "warning")}>
      {typeof count === "number" && count > 0 ? "Live" : "Empty"}
    </span>,
  ]);

  const adapterRows = [
    ["OKX USDT Swap", "Live", "Primary OHLCV, funding, OI, long/short"],
    ["Binance USD-M", "Degraded", "Restricted on current VPS region"],
    ["CoinGlass", "Live", "Funding/OI snapshots and aggregated liquidations"],
    ["CoinGecko", "Live", "Spot price and basis context"],
    ["Hyperliquid", "Pending", "Direct perp DEX venue adapter backlog"],
    ["dYdX", "Pending", "Direct perp DEX venue adapter backlog"],
    ["GMX", "Pending", "Direct perp DEX venue adapter backlog"],
  ].map(([venue, status, note]) => [
    venue,
    <span key="status" className={toneText(status === "Live" ? "positive" : "warning")}>
      {status}
    </span>,
    note,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Perp DEX</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">{activeTab.title}</h1>
          </div>
          <div className="flex items-center gap-2">
            <SegmentedControl
              items={perpDexViews.map((item) => ({ label: item.label, href: item.href }))}
              active={activeTab.label}
            />
            <StatusBadge label={livePerpRows ? "Perp inputs live" : "Inputs pending"} tone={livePerpRows ? "positive" : "warning"} />
            <StatusBadge label="DEX adapters pending" tone="warning" />
          </div>
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Universe" value={TRACKED_SYMBOLS_LABEL} />
            <SelectPill label="Perp Source" value="OKX USDT Swap" />
            <SelectPill label="Derivatives" value="Funding / OI / L/S" />
            <SelectPill label="DEX Venues" value="Pending direct adapters" />
            <SelectPill label="Storage" value="PostgreSQL" />
          </div>
        </TerminalPanel>

        <KpiStrip metrics={kpis} />

        {(activeView === "overview" || activeView === "open-interest" || activeView === "liquidity") && (
          <TerminalPanel title="Perp Universe Readiness" caption="Live persisted streams currently available for presentation">
            <TerminalTable
              columns={["Asset", "Perp Close", "Funding", "Open Interest", "Basis", "Long Accounts", "Status"]}
              rows={matrix.rows.map(perpUniverseCells)}
            />
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues") && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <TerminalPanel title="Venue Adapter Status" caption="Real provider status; direct DEX volume/OI pending">
              <TerminalTable columns={["Venue / Provider", "Status", "Scope"]} rows={adapterRows} />
              <div className="mt-3">
                <LinkButton href="/funding?view=perp-dex">Open Funding Matrix</LinkButton>
              </div>
            </TerminalPanel>

            <TerminalPanel title="Provider Health" caption="Current live providers backing this screen">
              {providerRows.length > 0 ? (
                <TerminalTable columns={["Provider", "Status", "Last Sync", "Last Error"]} rows={providerRows} />
              ) : (
                <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                  No provider health data returned by backend.
                </div>
              )}
            </TerminalPanel>
          </div>
        )}

        {(activeView === "overview" || activeView === "open-interest" || activeView === "liquidity") && (
          <TerminalPanel title="Persisted Perp Data Coverage" caption="Rows stored in PostgreSQL by stream">
            <TerminalTable columns={["Stream", "Rows", "Source", "Status"]} rows={dataCoverageRows} />
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "opportunities") && (
          <TerminalPanel
            title="Perp Research Candidates"
            caption="Basis/funding candidates from persisted streams; DEX-specific scoring waits for direct venue adapters"
          >
            <TerminalTable
              columns={["Asset", "Type", "Long Leg", "Short Leg", "Basis Edge", "Funding", "Open Interest", "Risk Note"]}
              rows={scanner.opportunities.slice(0, 5).map(opportunityCells)}
            />
          </TerminalPanel>
        )}

        {activeView === "opportunities" && (
          <TerminalPanel title="Execution Boundary" caption="Research-only state for the demo">
            <div className="rounded-md border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
              These rows are read-only research candidates. Direct DEX execution, venue fees, slippage, borrow costs and route-level risk checks are not connected yet.
            </div>
          </TerminalPanel>
        )}
      </div>
    </Shell>
  );
}
