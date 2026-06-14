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

function formatAge(value: number | null | undefined): string {
  if (value === null || value === undefined) return "No data";
  if (value < 60) return `${value.toFixed(value < 10 ? 1 : 0)}m`;
  return `${(value / 60).toFixed(1)}h`;
}

function statusTone(status: string | null | undefined): "positive" | "warning" | "negative" | "neutral" {
  if (
    status === "fresh" ||
    status === "healthy" ||
    status === "completed" ||
    status === "success" ||
    status === "covered" ||
    status === "complete_history" ||
    status === "core_perp_ready"
  ) return "positive";
  if (status === "stale" || status === "partial" || status === "partial_history") return "warning";
  if (status === "degraded" || status === "failed" || status === "failure" || status === "error" || status === "missing" || status === "not_ready") return "negative";
  return "neutral";
}

function freshnessAge(stream: { freshness_mode?: string; age_minutes: number | null; sync_age_minutes?: number | null }): string {
  if (stream.freshness_mode === "sparse_event") {
    return `event ${formatAge(stream.age_minutes)} / sync ${formatAge(stream.sync_age_minutes)}`;
  }
  return formatAge(stream.age_minutes);
}

function formatCoverage(value: number | null): string {
  return value === null ? "-" : `${value.toFixed(1)}%`;
}

function rowsCoverage(rows: number, expectedRows: number | null): string {
  return expectedRows === null ? formatRows(rows) : `${formatRows(rows)} / ${formatRows(expectedRows)}`;
}

function formatStreamList(streams: string[]): string {
  if (!streams.length) return "-";
  const visible = streams.slice(0, 4).join(", ");
  return streams.length > 4 ? `${visible} +${streams.length - 4}` : visible;
}

export default async function DataHealthPage() {
  const health = await getLiveDataHealth();
  const providers = Object.values(health?.providers ?? {});
  const healthyProviders = providers.filter((provider) => provider.healthy).length;
  const rowCounts = health?.row_counts ?? {};
  const freshnessSummary = health?.freshness?.summary;
  const coverageSummary = health?.coverage?.summary;
  const universeSummary = health?.universe?.summary;
  const cron = health?.sync_diagnostics?.cron;
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
      label: "Fresh Streams",
      value: freshnessSummary ? `${freshnessSummary.fresh}/${freshnessSummary.total}` : "0/0",
      caption: freshnessSummary
        ? `${freshnessSummary.stale} stale / ${freshnessSummary.degraded} degraded`
        : "Freshness SLA",
      tone: statusTone(freshnessSummary?.worst_status),
    },
    {
      label: "Coverage",
      value: coverageSummary ? `${coverageSummary.covered}/${coverageSummary.total}` : "0/0",
      caption: coverageSummary
        ? `${coverageSummary.partial} partial / ${coverageSummary.missing} missing`
        : "History matrix",
      tone: statusTone(coverageSummary?.worst_status),
    },
    {
      label: "Cron Path",
      value: cron?.status ?? "unknown",
      caption: cron ? `Last run ${formatAge(cron.last_run_age_minutes)}` : "No sync diagnostics",
      tone: statusTone(cron?.status),
    },
    {
      label: "Market Rows",
      value: formatRows(marketRows),
      caption: "PostgreSQL",
      tone: marketRows > 0 ? "positive" : "warning",
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

  const freshnessRows = [...(health?.freshness?.streams ?? [])]
    .sort((a, b) => {
      const rank = { degraded: 0, stale: 1, fresh: 2 };
      return rank[a.status] - rank[b.status] || a.stream.localeCompare(b.stream) || a.symbol.localeCompare(b.symbol);
    })
    .map((stream) => [
      stream.symbol,
      stream.exchange,
      stream.stream,
      stream.interval,
      <span key="status" className={toneText(statusTone(stream.status))}>
        {stream.status}
      </span>,
      freshnessAge(stream),
      `${stream.expected_cadence_minutes}m / ${stream.stale_after_minutes}m`,
      stream.reason,
    ]);

  const syncTypeRows = Object.entries(health?.sync_health_by_type ?? {}).flatMap(([providerName, syncTypes]) =>
    Object.entries(syncTypes).map(([syncType, sync]) => [
      providerName,
      syncType,
      <span key="status" className={toneText(statusTone(sync.status))}>
        {sync.status}
      </span>,
      formatAge(sync.last_run_age_minutes),
      sync.last_run ? `${formatRows(sync.last_run.records_fetched)} / ${formatRows(sync.last_run.records_inserted)}` : "-",
      sync.last_run?.error_class ?? "-",
      sync.reason,
    ])
  );

  const coverageRows = [...(health?.coverage?.rows ?? [])]
    .sort((a, b) => {
      const rank = { missing: 0, partial: 1, covered: 2 };
      return rank[a.status] - rank[b.status] || a.symbol.localeCompare(b.symbol) || a.stream.localeCompare(b.stream);
    })
    .map((row) => [
      row.symbol,
      row.exchange,
      row.stream,
      row.interval,
      <span key="status" className={toneText(statusTone(row.status))}>
        {row.status}
      </span>,
      rowsCoverage(row.rows, row.expected_rows),
      formatCoverage(row.coverage_pct),
      row.latest_timestamp_iso
        ? formatTime(row.latest_timestamp_iso)
        : row.coverage_mode === "sparse_event"
          ? `sync ${formatAge(row.sync_age_minutes)}`
          : "No data",
      row.reason,
    ]);

  const universeRows = [...(health?.universe?.symbols ?? [])]
    .sort((a, b) => {
      const rank = { not_ready: 0, partial_history: 1, core_perp_ready: 2, complete_history: 3 };
      return rank[a.status] - rank[b.status] || a.symbol.localeCompare(b.symbol);
    })
    .map((row) => [
      row.symbol,
      row.exchange,
      <span key="status" className={toneText(statusTone(row.status))}>
        {row.status}
      </span>,
      row.chart_ready ? "yes" : "no",
      `${row.coverage["24h"]?.covered ?? 0}/${row.coverage["24h"]?.total ?? 0}`,
      `${row.coverage["7d"]?.covered ?? 0}/${row.coverage["7d"]?.total ?? 0}`,
      formatStreamList(row.partial_streams_7d),
      formatStreamList(row.missing_streams_7d),
      row.reason,
    ]);

  const cronRows = [
    ["Status", <span key="status" className={toneText(statusTone(cron?.status))}>{cron?.status ?? "unknown"}</span>],
    ["Expected interval", `${cron?.expected_interval_minutes ?? 15}m`],
    ["Last run", cron?.last_run ? formatTime(cron.last_run.last_sync_at) : "No sync"],
    ["Last successful run", cron?.last_successful_run ? formatTime(cron.last_successful_run.last_sync_at) : "No sync"],
    ["Last run age", formatAge(cron?.last_run_age_minutes)],
    ["Reason", cron?.reason ?? "No diagnostics"],
  ];

  const recentErrorRows = Object.entries(health?.sync_diagnostics?.recent_error_classes ?? {}).map(([errorClass, count]) => [
    errorClass,
    <span key="count" className="font-mono text-slate-100">
      {formatRows(count)}
    </span>,
  ]);

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

        <TerminalPanel title="Freshness SLA" caption="Expected data age by symbol, exchange, stream and interval">
          {freshnessRows.length > 0 ? (
            <TerminalTable
              columns={["Symbol", "Exchange", "Stream", "Interval", "Status", "Event / sync age", "Cadence / stale", "Reason"]}
              rows={freshnessRows}
            />
          ) : (
            <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
              Backend did not return freshness SLA data.
            </div>
          )}
        </TerminalPanel>

        <TerminalPanel
          title="Coverage Matrix"
          caption={`Historical coverage by stream over ${health?.coverage?.scope.range ?? "7d"} for ${
            health?.coverage?.scope.symbols.join(", ") ?? "watched symbols"
          }`}
        >
          {coverageRows.length > 0 ? (
            <TerminalTable
              columns={["Symbol", "Exchange", "Stream", "Interval", "Status", "Rows", "Coverage", "Latest", "Reason"]}
              rows={coverageRows}
            />
          ) : (
            <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
              Backend did not return coverage matrix data.
            </div>
          )}
        </TerminalPanel>

        <TerminalPanel
          title="Production Universe"
          caption={`UI universe: ${health?.universe?.policy.ui_universe.join(", ") || "none"} / deferred: ${
            health?.universe?.policy.deferred_symbols.join(", ") || "none"
          }`}
        >
          {universeRows.length > 0 ? (
            <TerminalTable
              columns={["Symbol", "Exchange", "Status", "Charts", "24h", "7d", "Partial 7d", "Missing 7d", "Reason"]}
              rows={universeRows}
            />
          ) : (
            <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
              Backend did not return production universe data.
            </div>
          )}
          {universeSummary && (
            <div className="mt-3 text-xs text-slate-500">
              Complete {universeSummary.complete_history} / core {universeSummary.core_perp_ready} / partial {universeSummary.partial_history} / not ready {universeSummary.not_ready}
            </div>
          )}
        </TerminalPanel>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_0.7fr]">
          <TerminalPanel title="Sync Types" caption="Latest provider sync runs split by stream">
            {syncTypeRows.length > 0 ? (
              <TerminalTable
                columns={["Provider", "Sync Type", "Status", "Age", "Fetched / Inserted", "Error Class", "Reason"]}
                rows={syncTypeRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Backend did not return sync type diagnostics.
              </div>
            )}
          </TerminalPanel>

          <div className="space-y-4">
            <TerminalPanel title="Cron Diagnostics" caption="Host-level sync path">
              <TerminalTable columns={["Metric", "Value"]} rows={cronRows} />
            </TerminalPanel>

            <TerminalPanel title="Recent Error Classes" caption={`${health?.sync_diagnostics?.recent_window_hours ?? 24}h window`}>
              {recentErrorRows.length > 0 ? (
                <TerminalTable columns={["Error Class", "Runs"]} rows={recentErrorRows} />
              ) : (
                <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                  No recent sync errors.
                </div>
              )}
            </TerminalPanel>
          </div>
        </div>

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
