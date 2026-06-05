import { Shell } from "@/components/layout/Shell";
import {
  KpiStrip,
  LinkButton,
  SegmentedControl,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveDataHealth } from "@/lib/terminal/live-data";
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

export default async function PerpDexPage({ searchParams }: { searchParams?: { view?: string } }) {
  const activeView = normalizeView(searchParams?.view);
  const activeTab = perpDexViews.find((item) => item.view === activeView) ?? perpDexViews[0];
  const health = await getLiveDataHealth();
  const rowCounts = health?.row_counts ?? {};
  const providers = Object.values(health?.providers ?? {});
  const healthyProviders = providers.filter((provider) => provider.healthy).length;

  const kpis: KpiMetric[] = [
    {
      label: "DEX Venue Data",
      value: "Pending",
      caption: "Live adapter not connected",
      tone: "warning",
    },
    {
      label: "Funding Rows",
      value: formatRows(rowCounts.funding_rates),
      caption: "PostgreSQL",
      tone: (rowCounts.funding_rates ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Open Interest Rows",
      value: formatRows(rowCounts.open_interest),
      caption: "PostgreSQL",
      tone: (rowCounts.open_interest ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Long/Short Rows",
      value: formatRows(rowCounts.long_short_ratio),
      caption: "PostgreSQL",
      tone: (rowCounts.long_short_ratio ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Provider Health",
      value: providers.length ? `${healthyProviders}/${providers.length}` : "0/0",
      caption: "Binance/CoinGlass/CoinGecko",
      tone: healthyProviders === providers.length && providers.length > 0 ? "positive" : "warning",
    },
    {
      label: "Data Quality",
      value: health ? `${health.data_quality.score.toFixed(0)}/100` : "No data",
      caption: "24h window",
      tone: health && health.data_quality.score >= 80 ? "positive" : "warning",
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

  const rowCountRows = Object.entries(rowCounts).map(([tableName, count]) => [
    tableName,
    <span key="count" className="font-mono text-slate-100">
      {formatRows(count)}
    </span>,
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
            <StatusBadge label="DEX data pending" tone="warning" />
          </div>
        </div>

        <KpiStrip metrics={kpis} />

        {(activeView === "overview" || activeView === "venues") && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.85fr_1.15fr]">
            <TerminalPanel title="Perp DEX Venue Coverage" caption="No live DEX venue adapter is configured in backend yet">
              <div className="rounded-md border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
                Live Hyperliquid/dYdX/GMX venue metrics are not connected yet, so mock DEX volumes and OI are not shown.
              </div>
              <div className="mt-3">
                <LinkButton href="/funding?view=perp-dex">View Funding Data</LinkButton>
              </div>
            </TerminalPanel>

            <TerminalPanel title="Provider Health" caption="Current live providers backing the persisted data layer">
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
          <TerminalPanel title="Persisted Market Data" caption="Rows currently stored in PostgreSQL">
            {rowCountRows.length > 0 ? (
              <TerminalTable columns={["Table", "Rows"]} rows={rowCountRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                No row-count data returned by backend.
              </div>
            )}
          </TerminalPanel>
        )}

        {activeView === "opportunities" && (
          <TerminalPanel title="Perp DEX Opportunities" caption="Requires live venue adapters before ranking DEX-specific opportunities">
            <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm leading-6 text-slate-400">
              Funding-derived opportunities are available from persisted Binance/CoinGlass data. DEX venue-specific opportunity scoring remains backlog work.
            </div>
            <div className="mt-3">
              <LinkButton href="/funding?view=arbitrage">Open Funding Arbitrage</LinkButton>
            </div>
          </TerminalPanel>
        )}
      </div>
    </Shell>
  );
}
