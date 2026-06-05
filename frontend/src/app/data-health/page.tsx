import { Shell } from "@/components/layout/Shell";
import { KpiStrip, StatusBadge, TerminalPanel, TerminalTable, toneText } from "@/components/terminal/terminal-ui";
import { getLiveDataHealth } from "@/lib/terminal/live-data";
import { KpiMetric } from "@/types/terminal";

export const dynamic = "force-dynamic";

function formatRows(value?: number): string {
  return (value ?? 0).toLocaleString("en-US");
}

function formatTime(value: string | null): string {
  if (!value) return "No sync";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No sync";
  return date.toLocaleString("en-US", { dateStyle: "short", timeStyle: "short" });
}

function syncTime(lastSync: Record<string, unknown> | null): string {
  const value = lastSync?.last_sync_at;
  return typeof value === "string" ? formatTime(value) : "No sync";
}

export default async function DataHealthPage() {
  const health = await getLiveDataHealth();
  const providers = Object.values(health?.providers ?? {});
  const healthyProviders = providers.filter((provider) => provider.healthy).length;
  const rowCounts = health?.row_counts ?? {};
  const marketRows =
    (rowCounts.ohlcv ?? 0) +
    (rowCounts.funding_rates ?? 0) +
    (rowCounts.open_interest ?? 0) +
    (rowCounts.liquidations ?? 0) +
    (rowCounts.long_short_ratio ?? 0);

  const kpis: KpiMetric[] = [
    {
      label: "Provider Health",
      value: providers.length ? `${healthyProviders}/${providers.length}` : "0/0",
      caption: "Watched providers",
      tone: healthyProviders === providers.length && providers.length > 0 ? "positive" : "warning",
    },
    {
      label: "Market Rows",
      value: formatRows(marketRows),
      caption: "PostgreSQL",
      tone: marketRows > 0 ? "positive" : "warning",
    },
    {
      label: "Funding Rows",
      value: formatRows(rowCounts.funding_rates),
      caption: "Funding table",
      tone: (rowCounts.funding_rates ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Open Interest Rows",
      value: formatRows(rowCounts.open_interest),
      caption: "OI table",
      tone: (rowCounts.open_interest ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Sync Runs",
      value: formatRows(rowCounts.provider_sync_runs),
      caption: "Provider sync history",
      tone: (rowCounts.provider_sync_runs ?? 0) > 0 ? "positive" : "warning",
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
    formatTime(provider.last_success_at),
    syncTime(provider.last_sync),
    provider.last_error_message ?? "-",
  ]);

  const rowCountRows = Object.entries(rowCounts).map(([tableName, count]) => [
    tableName,
    <span key="count" className="font-mono text-slate-100">
      {formatRows(count)}
    </span>,
  ]);

  const severityRows = Object.entries(health?.data_quality.severity_counts ?? {}).map(([severity, count]) => [
    severity,
    <span key="count" className="font-mono text-slate-100">
      {formatRows(count)}
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Data Health</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">Provider & Storage Status</h1>
          </div>
          <StatusBadge label={health ? "Live PostgreSQL data" : "Backend unavailable"} tone={health ? "positive" : "warning"} />
        </div>

        <KpiStrip metrics={kpis} />

        <TerminalPanel title="Providers" caption="Read-only health snapshot from backend">
          {providerRows.length > 0 ? (
            <TerminalTable columns={["Provider", "Status", "Last Success", "Last Sync", "Last Error"]} rows={providerRows} />
          ) : (
            <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
              Backend did not return provider health data.
            </div>
          )}
        </TerminalPanel>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_0.7fr]">
          <TerminalPanel title="Row Counts" caption="Current PostgreSQL table sizes used by the MVP data layer">
            {rowCountRows.length > 0 ? (
              <TerminalTable columns={["Table", "Rows"]} rows={rowCountRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Backend did not return table row counts.
              </div>
            )}
          </TerminalPanel>

          <TerminalPanel title="Quality Logs" caption="Recent data quality severity counts">
            {severityRows.length > 0 ? (
              <TerminalTable columns={["Severity", "Rows"]} rows={severityRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                No recent quality penalties.
              </div>
            )}
          </TerminalPanel>
        </div>
      </div>
    </Shell>
  );
}
