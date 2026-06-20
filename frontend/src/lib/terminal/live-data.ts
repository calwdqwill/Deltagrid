import { fetchServerApi } from "@/lib/server-api";
import {
  FundingData,
  FundingAnomalyDetailRow,
  FundingDataQualityRunwayRow,
  FundingFreshnessAnomalyRow,
  FundingHistoryControlRow,
  FundingHistoryDiagnosticRow,
  FundingHistoryReadinessRow,
  FundingQaDrilldownRow,
  FundingRate,
  FundingReleaseChecklistRow,
  FundingSourceComparisonRow,
  FundingSourceStatusRow,
  KpiMetric,
} from "@/types/terminal";

type StatusTone = "positive" | "negative" | "warning" | "neutral";

type FundingExchange = "okx" | "coinglass";
type FundingHistorySource = FundingExchange | "all";

interface FundingHistoryOptions {
  historySymbol?: string;
  historySource?: string;
}

interface FundingHistorySelection {
  symbol: string;
  source: FundingHistorySource;
  explicitSource: boolean;
}

interface DataFundingRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  funding_rate: number | string | null;
  next_funding_time?: number | null;
  interval?: string | null;
}

export interface ProviderSnapshot {
  provider_name: string;
  status: string;
  healthy: boolean;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_error_message: string | null;
  avg_response_ms: number | null;
  failure_count_24h: number;
  updated_at: string | null;
  last_sync: Record<string, unknown> | null;
}

export interface FreshnessStreamSnapshot {
  symbol: string;
  exchange: string;
  stream: string;
  interval: string;
  latest_timestamp: number | null;
  latest_timestamp_iso: string | null;
  age_minutes: number | null;
  expected_cadence_minutes: number;
  stale_after_minutes: number;
  degraded_after_minutes: number;
  status: "fresh" | "stale" | "degraded";
  reason: string;
  freshness_mode?: "event" | "sparse_event";
  event_age_minutes?: number | null;
  sync_provider?: string;
  sync_type?: string;
  latest_sync_status?: string | null;
  latest_sync_at?: string | null;
  latest_successful_sync_at?: string | null;
  sync_age_minutes?: number | null;
  sync_stale_after_minutes?: number;
  sync_degraded_after_minutes?: number;
}

export interface FreshnessReport {
  scope: {
    symbols: string[];
    primary_exchange: string;
    streams: string[];
  };
  summary: {
    fresh: number;
    stale: number;
    degraded: number;
    total: number;
    worst_status: "fresh" | "stale" | "degraded" | "unknown";
  };
  by_stream: Record<string, Record<"fresh" | "stale" | "degraded", number>>;
  streams: FreshnessStreamSnapshot[];
}

export interface CoverageRowSnapshot {
  symbol: string;
  exchange: string;
  stream: string;
  interval: string;
  status: "covered" | "partial" | "missing";
  rows: number;
  expected_rows: number | null;
  coverage_pct: number | null;
  window_start: number | null;
  window_end: number | null;
  window_start_iso: string | null;
  window_end_iso: string | null;
  latest_timestamp: number | null;
  latest_timestamp_iso: string | null;
  window_source: "latest_available" | "wall_clock";
  reason: string;
  coverage_mode: "regular" | "sparse_event";
  sync_provider?: string;
  sync_type?: string;
  latest_successful_sync_at?: string | null;
  sync_age_minutes?: number | null;
}

export interface CoverageReport {
  scope: {
    symbols: string[];
    exchange: string;
    range: string;
    streams: string[];
  };
  summary: {
    covered: number;
    partial: number;
    missing: number;
    total: number;
    coverage_pct: number;
    worst_status: "covered" | "partial" | "missing" | "unknown";
  };
  by_symbol: Record<string, Record<"covered" | "partial" | "missing", number>>;
  by_stream: Record<string, Record<"covered" | "partial" | "missing", number>>;
  rows: CoverageRowSnapshot[];
}

export interface UniverseSymbolSnapshot {
  symbol: string;
  exchange: string;
  status: "complete_history" | "core_perp_ready" | "partial_history" | "not_ready";
  chart_ready: boolean;
  complete_history: boolean;
  ui_visible: boolean;
  coverage: Record<string, CoverageReport["summary"]>;
  freshness: FreshnessReport["summary"] & { fresh_pct: number };
  covered_streams_7d: string[];
  partial_streams_7d: string[];
  missing_streams_7d: string[];
  reason: string;
}

export interface UniverseReport {
  scope: {
    symbols: string[];
    exchange: string;
    ranges: string[];
    primary_range: string;
  };
  summary: {
    complete_history: number;
    core_perp_ready: number;
    partial_history: number;
    not_ready: number;
    chart_ready: number;
    total: number;
  };
  policy: {
    ui_universe: string[];
    deferred_symbols: string[];
    rule: string;
  };
  symbols: UniverseSymbolSnapshot[];
}

export interface SyncRunSnapshot {
  provider_name: string;
  sync_type: string;
  status: string;
  last_sync_at: string | null;
  start_time: number | null;
  end_time: number | null;
  records_fetched: number;
  records_inserted: number;
  error_message: string | null;
  error_class: string | null;
  source_table: string;
}

export interface SyncTypeHealth {
  provider_name: string;
  sync_type: string;
  status: "healthy" | "stale" | "degraded" | "unknown";
  healthy: boolean;
  reason: string;
  last_run_age_minutes: number | null;
  expected_cron_interval_minutes: number;
  last_run: SyncRunSnapshot | null;
  last_successful_run: SyncRunSnapshot | null;
  last_problem_run: SyncRunSnapshot | null;
  recent_window_hours: number;
  recent_status_counts: Record<string, number>;
  recent_error_classes: Record<string, number>;
}

export interface SyncDiagnostics {
  cron: {
    status: "healthy" | "stale" | "degraded" | "unknown";
    reason: string;
    expected_interval_minutes: number;
    last_run_age_minutes: number | null;
    last_run: SyncRunSnapshot | null;
    last_successful_run: SyncRunSnapshot | null;
  };
  recent_window_hours: number;
  recent_runs: number;
  recent_status_counts: Record<string, number>;
  recent_error_classes: Record<string, number>;
}

export interface DataHealthPayload {
  providers: Record<string, ProviderSnapshot>;
  last_sync: Record<string, Record<string, unknown> | null>;
  row_counts: Record<string, number>;
  data_quality: {
    score: number;
    window_hours: number;
    severity_counts: Record<string, number>;
    method: string;
  };
  freshness: FreshnessReport;
  coverage: CoverageReport;
  universe: UniverseReport;
  sync_health_by_type: Record<string, Record<string, SyncTypeHealth>>;
  sync_diagnostics: SyncDiagnostics;
}

export interface LiveFundingOverview {
  data: FundingData;
  statusLabel: string;
  statusTone: StatusTone;
  sourceCaption: string;
  historyLabel: string;
  historySelection: {
    asset: string;
    source: FundingHistorySource;
  };
}

const WATCHED_SYMBOLS = ["BTC", "ETH", "SOL"];
const FUNDING_EXCHANGES: FundingExchange[] = ["okx", "coinglass"];

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(Math.abs(value) < 1 ? 3 : 2)}%`;
}

function formatRows(value: number): string {
  return value.toLocaleString("en-US");
}

function formatAgeMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "unknown";
  if (value < 1) return "<1m";
  if (value < 60) return `${Math.round(value)}m`;
  if (value < 24 * 60) return `${(value / 60).toFixed(1)}h`;
  return `${(value / (24 * 60)).toFixed(1)}d`;
}

function formatLatestAge(timestamp: number | null): string {
  if (timestamp === null || !Number.isFinite(timestamp)) return "No rows";
  return `${formatAgeMinutes((Date.now() - timestamp) / 60_000)} ago`;
}

function formatRateOrEmpty(value: number | null): string {
  return value === null ? "No rate" : formatPercent(value);
}

function statusTone(status: string | null | undefined): StatusTone {
  const normalized = (status ?? "").toLowerCase();
  if (["fresh", "covered", "healthy", "completed", "success"].includes(normalized)) return "positive";
  if (["stale", "partial", "warning"].includes(normalized)) return "warning";
  if (["degraded", "missing", "failed", "failure", "error"].includes(normalized)) return "negative";
  return "neutral";
}

function worstTone(toneValues: StatusTone[]): StatusTone {
  if (toneValues.includes("negative")) return "negative";
  if (toneValues.includes("warning")) return "warning";
  if (toneValues.includes("positive")) return "positive";
  return "neutral";
}

function summarizeStatuses<T extends { status: string }>(
  rows: T[],
  emptyLabel: string
): { label: string; tone: StatusTone } {
  if (!rows.length) return { label: emptyLabel, tone: "neutral" };

  const counts = rows.reduce<Record<string, number>>((summary, row) => {
    const status = row.status || "unknown";
    summary[status] = (summary[status] ?? 0) + 1;
    return summary;
  }, {});
  const label = Object.entries(counts)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([status, count]) => `${status} ${count}/${rows.length}`)
    .join(", ");
  return {
    label,
    tone: worstTone(rows.map((row) => statusTone(row.status))),
  };
}

function venueLabel(exchange: string): string {
  const normalized = exchange.toLowerCase();
  if (normalized === "coinglass") return "CoinGlass";
  if (normalized === "okx") return "OKX";
  if (normalized === "binance") return "Binance";
  return exchange;
}

function historySourceLabel(source: FundingHistorySource): string {
  if (source === "all") return "All sources";
  return venueLabel(source);
}

function normalizeHistorySelection(options?: FundingHistoryOptions): FundingHistorySelection {
  const requestedSymbol = options?.historySymbol?.toUpperCase();
  const requestedSource = options?.historySource?.toLowerCase();
  const symbol = requestedSymbol && WATCHED_SYMBOLS.includes(requestedSymbol) ? requestedSymbol : "BTC";
  const source =
    requestedSource === "okx" || requestedSource === "coinglass" || requestedSource === "all"
      ? requestedSource
      : "coinglass";

  return {
    symbol,
    source,
    explicitSource: Boolean(requestedSource),
  };
}

function exchangeKey(venue: string): string {
  return venue.toLowerCase();
}

function rowRatePercent(row: DataFundingRow): number | null {
  const rate = toNumber(row.funding_rate);
  return rate === null ? null : rate * 100;
}

function latestTimestamp(rows: DataFundingRow[]): number | null {
  if (!rows.length) return null;
  const timestamps = rows.map((row) => row.timestamp).filter(Number.isFinite);
  if (!timestamps.length) return null;
  return Math.max(...timestamps);
}

function latestRows(rows: DataFundingRow[]): DataFundingRow[] {
  const latest = new Map<string, DataFundingRow>();

  for (const row of rows) {
    const symbol = row.symbol.toUpperCase();
    const exchange = row.exchange.toLowerCase();
    const key = `${symbol}:${exchange}`;
    const existing = latest.get(key);

    if (!existing || row.timestamp > existing.timestamp) {
      latest.set(key, row);
    }
  }

  return Array.from(latest.values()).sort((a, b) => b.timestamp - a.timestamp);
}

function latestFundingRow(rows: DataFundingRow[], symbol: string, exchange: FundingExchange): DataFundingRow | null {
  return rows
    .filter((row) => row.symbol.toUpperCase() === symbol && row.exchange.toLowerCase() === exchange)
    .reduce<DataFundingRow | null>((latest, row) => {
      if (!latest || row.timestamp > latest.timestamp) return row;
      return latest;
    }, null);
}

function fundingFreshnessRow(
  health: DataHealthPayload | null,
  symbol: string,
  exchange: FundingExchange
): FreshnessStreamSnapshot | null {
  return (
    health?.freshness?.streams?.find(
      (row) =>
        row.stream === "funding_rates" &&
        row.symbol.toUpperCase() === symbol &&
        row.exchange.toLowerCase() === exchange
    ) ?? null
  );
}

function fundingCoverageRow(
  health: DataHealthPayload | null,
  symbol: string,
  exchange: FundingExchange
): CoverageRowSnapshot | null {
  return (
    health?.coverage?.rows?.find(
      (row) =>
        row.stream === "funding_rates" &&
        row.symbol.toUpperCase() === symbol &&
        row.exchange.toLowerCase() === exchange
    ) ?? null
  );
}

function fundingSyncHealth(health: DataHealthPayload | null, exchange: FundingExchange): SyncTypeHealth | null {
  return health?.sync_health_by_type?.[exchange]?.[exchange === "coinglass" ? "snapshots" : "funding_rates"] ?? null;
}

function fundingDataStatus(
  health: DataHealthPayload | null,
  symbol: string,
  exchange: FundingExchange,
  latest: number | null
): { label: string; tone: StatusTone } {
  const freshness = fundingFreshnessRow(health, symbol, exchange);
  if (freshness) {
    return {
      label: `${freshness.status} / ${formatAgeMinutes(freshness.age_minutes)} age`,
      tone: statusTone(freshness.status),
    };
  }

  if (latest !== null) return { label: `Loaded / ${formatLatestAge(latest)}`, tone: "neutral" };
  return { label: "No loaded rows", tone: "warning" };
}

function fundingAnomalyStatus(rates: number[]): { label: string; tone: StatusTone } {
  if (rates.length < 4) return { label: "Need more history", tone: "neutral" };

  const latest = rates[rates.length - 1];
  const baseline = rates.slice(0, -1);
  const average = baseline.reduce((sum, value) => sum + value, 0) / baseline.length;
  const variance = baseline.reduce((sum, value) => sum + (value - average) ** 2, 0) / baseline.length;
  const deviation = Math.sqrt(variance);

  if (deviation < 0.000_001) return { label: "Stable baseline", tone: "positive" };

  const zScore = Math.abs((latest - average) / deviation);
  if (zScore >= 3) return { label: `Stat outlier z=${zScore.toFixed(1)}`, tone: "warning" };
  if (zScore >= 2) return { label: `Elevated z=${zScore.toFixed(1)}`, tone: "warning" };
  return { label: `Normal z=${zScore.toFixed(1)}`, tone: "positive" };
}

function fundingAnomalyDetail(rates: number[]): {
  baselineAverage: string;
  observedRange: string;
  zScore: string;
  status: string;
  statusTone: StatusTone;
  nextReview: string;
} {
  if (rates.length < 4) {
    return {
      baselineAverage: "Need history",
      observedRange: "Need history",
      zScore: "n/a",
      status: "Need more history",
      statusTone: "neutral",
      nextReview: "Collect at least 4 observations",
    };
  }

  const latest = rates[rates.length - 1];
  const baseline = rates.slice(0, -1);
  const average = baseline.reduce((sum, value) => sum + value, 0) / baseline.length;
  const min = Math.min(...rates);
  const max = Math.max(...rates);
  const variance = baseline.reduce((sum, value) => sum + (value - average) ** 2, 0) / baseline.length;
  const deviation = Math.sqrt(variance);

  if (deviation < 0.000_001) {
    return {
      baselineAverage: formatPercent(average),
      observedRange: `${formatPercent(min)} to ${formatPercent(max)}`,
      zScore: "stable",
      status: "Stable baseline",
      statusTone: "positive",
      nextReview: "Monitor for source drift",
    };
  }

  const zScore = Math.abs((latest - average) / deviation);
  const status = fundingAnomalyStatus(rates);
  return {
    baselineAverage: formatPercent(average),
    observedRange: `${formatPercent(min)} to ${formatPercent(max)}`,
    zScore: zScore.toFixed(2),
    status: status.label,
    statusTone: status.tone,
    nextReview: zScore >= 2 ? "Review freshness and source delta" : "Monitor; no anomaly action required",
  };
}

function buildFundingAnomalyDetails(rows: DataFundingRow[]): FundingAnomalyDetailRow[] {
  return WATCHED_SYMBOLS.flatMap((symbol) =>
    FUNDING_EXCHANGES.map((exchange) => {
      const rates = rows
        .filter((row) => row.symbol.toUpperCase() === symbol && row.exchange.toLowerCase() === exchange)
        .sort((left, right) => left.timestamp - right.timestamp)
        .map((row) => rowRatePercent(row))
        .filter((value): value is number => value !== null && Number.isFinite(value));
      const detail = fundingAnomalyDetail(rates);
      const latestRate = rates.length ? rates[rates.length - 1] : null;

      return {
        asset: symbol,
        source: venueLabel(exchange),
        samples: formatRows(rates.length),
        latestRate: formatRateOrEmpty(latestRate),
        baselineAverage: detail.baselineAverage,
        observedRange: detail.observedRange,
        zScore: detail.zScore,
        status: detail.status,
        statusTone: detail.statusTone,
        nextReview: detail.nextReview,
        boundary: "Anomaly QA only; not trading, carry, route ranking or execution signal",
      };
    })
  );
}

function historyWindowLabel(rows: DataFundingRow[]): string {
  const timestamps = rows.map((row) => row.timestamp).filter(Number.isFinite).sort((left, right) => left - right);
  if (!timestamps.length) return "No window";
  if (timestamps.length === 1) return "Single point";
  return `${formatAgeMinutes((timestamps[timestamps.length - 1] - timestamps[0]) / 60_000)} span`;
}

function buildFundingHistoryDiagnostics(
  rows: DataFundingRow[],
  health: DataHealthPayload | null
): FundingHistoryDiagnosticRow[] {
  return WATCHED_SYMBOLS.flatMap((symbol) =>
    FUNDING_EXCHANGES.map((exchange) => {
      const sourceRows = rows
        .filter((row) => row.symbol.toUpperCase() === symbol && row.exchange.toLowerCase() === exchange)
        .sort((left, right) => left.timestamp - right.timestamp);
      const rates = sourceRows
        .map((row) => rowRatePercent(row))
        .filter((value): value is number => value !== null && Number.isFinite(value));
      const latest = latestTimestamp(sourceRows);
      const latestRow = sourceRows[sourceRows.length - 1] ?? null;
      const freshness = fundingFreshnessRow(health, symbol, exchange);
      const average = rates.length ? rates.reduce((sum, value) => sum + value, 0) / rates.length : null;
      const min = rates.length ? Math.min(...rates) : null;
      const max = rates.length ? Math.max(...rates) : null;
      const status =
        sourceRows.length === 0
          ? { label: "No history", tone: "warning" as StatusTone }
          : freshness
            ? { label: freshness.status, tone: statusTone(freshness.status) }
            : { label: "Loaded", tone: "neutral" as StatusTone };
      const nextAction =
        sourceRows.length === 0
          ? "Run sync or verify provider mapping"
          : sourceRows.length < 4
            ? "Collect more funding observations"
            : freshness && ["degraded", "stale"].includes(freshness.status)
              ? "Inspect freshness before chart analysis"
              : "History window usable for QA review";

      return {
        asset: symbol,
        source: venueLabel(exchange),
        observations: formatRows(sourceRows.length),
        window: historyWindowLabel(sourceRows),
        latest: formatLatestAge(latest),
        interval: latestRow?.interval ?? "unknown",
        averageRate: formatRateOrEmpty(average),
        observedRange: min === null || max === null ? "No rate" : `${formatPercent(min)} to ${formatPercent(max)}`,
        status: status.label,
        statusTone: status.tone,
        nextAction,
        boundary: "History diagnostics only; not strategy, carry, ranking or execution signal",
      };
    })
  );
}

function historyIntervalLabel(rows: DataFundingRow[]): string {
  const intervals = Array.from(new Set(rows.map((row) => row.interval ?? "unknown"))).sort();
  if (!intervals.length) return "unknown";
  if (intervals.length === 1) return intervals[0];
  return `mixed: ${intervals.join(", ")}`;
}

function selectFundingHistoryRows(
  rows: DataFundingRow[],
  selection: FundingHistorySelection
): { selectedRows: DataFundingRow[]; assetRows: DataFundingRow[]; sourceRows: DataFundingRow[]; fallbackUsed: boolean } {
  const assetRows = rows.filter((row) => row.symbol.toUpperCase() === selection.symbol);
  const sourceRows =
    selection.source === "all"
      ? assetRows
      : assetRows.filter((row) => row.exchange.toLowerCase() === selection.source);

  if (selection.source === "all") {
    return { selectedRows: assetRows, assetRows, sourceRows, fallbackUsed: false };
  }

  if (sourceRows.length || selection.explicitSource) {
    return { selectedRows: sourceRows, assetRows, sourceRows, fallbackUsed: false };
  }

  if (assetRows.length) {
    return { selectedRows: assetRows, assetRows, sourceRows, fallbackUsed: true };
  }

  return { selectedRows: rows, assetRows, sourceRows, fallbackUsed: rows.length > 0 };
}

function historyControlStatus(rowCount: number): { label: string; tone: StatusTone } {
  if (rowCount === 0) return { label: "No rows", tone: "warning" };
  if (rowCount === 1) return { label: "Single point", tone: "warning" };
  if (rowCount < 4) return { label: "Thin history", tone: "warning" };
  return { label: "Ready for QA", tone: "positive" };
}

function buildFundingHistoryControls(
  selection: FundingHistorySelection,
  selectedRows: DataFundingRow[],
  assetRows: DataFundingRow[],
  sourceRows: DataFundingRow[],
  fallbackUsed: boolean
): FundingHistoryControlRow[] {
  const selectedStatus = historyControlStatus(selectedRows.length);
  const assetStatus = historyControlStatus(assetRows.length);
  const sourceStatus = historyControlStatus(sourceRows.length);
  const latest = latestTimestamp(selectedRows);
  const rates = selectedRows
    .map((row) => rowRatePercent(row))
    .filter((value): value is number => value !== null && Number.isFinite(value));
  const rangeReady = rates.length >= 4;

  return [
    {
      control: "Asset",
      selection: selection.symbol,
      status: assetStatus.label,
      statusTone: assetStatus.tone,
      reason: `${formatRows(assetRows.length)} rows for selected asset`,
      nextAction: assetRows.length ? "Review source coverage" : "Run sync or choose another asset",
      boundary: "History control only; not strategy or execution signal",
    },
    {
      control: "Source",
      selection: historySourceLabel(selection.source),
      status: sourceStatus.label,
      statusTone: sourceStatus.tone,
      reason:
        selection.source === "all"
          ? `${formatRows(sourceRows.length)} rows across all sources`
          : `${formatRows(sourceRows.length)} rows for selected source`,
      nextAction: sourceRows.length ? "Use selected source for chart QA" : "Switch source or wait for sync",
      boundary: "Source selector is display-only; not provider ranking",
    },
    {
      control: "Chart Series",
      selection: fallbackUsed ? "Fallback source used" : "Requested selection",
      status: selectedStatus.label,
      statusTone: selectedStatus.tone,
      reason: `${formatRows(selectedRows.length)} rows selected for the visible history chart`,
      nextAction: selectedRows.length > 1 ? "Inspect history trend visually" : "Collect at least 2 points",
      boundary: "Chart readiness only; not trading signal",
    },
    {
      control: "Window",
      selection: historyWindowLabel(selectedRows),
      status: selectedRows.length > 1 ? "Window available" : "Window unavailable",
      statusTone: selectedRows.length > 1 ? "positive" : "warning",
      reason: `Latest row: ${formatLatestAge(latest)}`,
      nextAction: selectedRows.length > 1 ? "Compare with diagnostics panel" : "Wait for another funding observation",
      boundary: "Window QA only; not carry calculation",
    },
    {
      control: "Interval",
      selection: historyIntervalLabel(selectedRows),
      status: selectedRows.length ? "Observed" : "Unknown",
      statusTone: selectedRows.length ? "neutral" : "warning",
      reason: "Interval comes from persisted funding rows",
      nextAction: selectedRows.length ? "Keep interval as display metadata" : "Verify provider mapping",
      boundary: "Interval metadata only; not execution cadence",
    },
    {
      control: "Range Hint",
      selection: rangeReady ? "QA review ready" : "Need more samples",
      status: rangeReady ? "Ready" : "Waiting",
      statusTone: rangeReady ? "positive" : "warning",
      reason: `${formatRows(rates.length)} numeric funding rates in selected series`,
      nextAction: rangeReady ? "Use diagnostics before any product decision" : "Collect at least 4 numeric rates",
      boundary: "Range hint only; no carry bps, ranking or route selection",
    },
  ];
}

function historyEmptyStateStatus(
  selection: FundingHistorySelection,
  selectedRows: DataFundingRow[],
  assetRows: DataFundingRow[],
  sourceRows: DataFundingRow[],
  fallbackUsed: boolean,
  numericRates: number[]
): { label: string; tone: StatusTone; evidence: string; nextAction: string } {
  if (!assetRows.length && !selectedRows.length) {
    return {
      label: "No selected asset rows",
      tone: "warning",
      evidence: `${selection.symbol} has no persisted funding rows for the history workflow`,
      nextAction: "Run funding sync or choose another asset",
    };
  }

  if (!assetRows.length && fallbackUsed) {
    return {
      label: "Fallback rows shown",
      tone: "warning",
      evidence: `${selection.symbol} is empty; chart uses other persisted funding rows`,
      nextAction: "Pick an asset with rows or wait for selected asset sync",
    };
  }

  if (selection.source !== "all" && !sourceRows.length) {
    return {
      label: "Selected source empty",
      tone: "warning",
      evidence: `${historySourceLabel(selection.source)} has no rows for ${selection.symbol}`,
      nextAction: "Switch source to All or wait for provider sync",
    };
  }

  if (selectedRows.length === 0) {
    return {
      label: "No chart series",
      tone: "warning",
      evidence: "Selected history series has no persisted rows",
      nextAction: "Run funding sync before chart QA",
    };
  }

  if (selectedRows.length === 1) {
    return {
      label: "Single chart point",
      tone: "warning",
      evidence: "Line chart needs at least 2 points for a visible history path",
      nextAction: "Collect one more funding observation",
    };
  }

  if (numericRates.length < 4) {
    return {
      label: "Thin chart history",
      tone: "warning",
      evidence: `${formatRows(numericRates.length)} numeric rates are available for selected series`,
      nextAction: "Collect more samples before product interpretation",
    };
  }

  return {
    label: "Chart QA ready",
    tone: "positive",
    evidence: `${formatRows(selectedRows.length)} rows can render the selected funding history`,
    nextAction: "Use diagnostics/readiness together for review",
  };
}

function buildFundingHistoryReadiness(
  selection: FundingHistorySelection,
  rows: DataFundingRow[],
  selectedRows: DataFundingRow[],
  assetRows: DataFundingRow[],
  sourceRows: DataFundingRow[],
  fallbackUsed: boolean
): FundingHistoryReadinessRow[] {
  const numericRates = selectedRows
    .map((row) => rowRatePercent(row))
    .filter((value): value is number => value !== null && Number.isFinite(value));
  const chartState = historyEmptyStateStatus(selection, selectedRows, assetRows, sourceRows, fallbackUsed, numericRates);
  const sourceLabel = historySourceLabel(selection.source);

  return [
    {
      check: "Persisted Rows",
      status: rows.length ? "Rows loaded" : "No funding rows",
      statusTone: rows.length ? "positive" : "warning",
      evidence: `${formatRows(rows.length)} funding rows available to the history workflow`,
      nextAction: rows.length ? "Use controls to inspect a series" : "Run funding sync before chart QA",
      boundary: "Readiness only; not trading or execution signal",
    },
    {
      check: "Selected Asset",
      status: assetRows.length ? "Asset rows loaded" : "Asset empty",
      statusTone: assetRows.length ? "positive" : "warning",
      evidence: `${formatRows(assetRows.length)} rows for ${selection.symbol}`,
      nextAction: assetRows.length ? "Review selected source readiness" : "Choose another asset or wait for sync",
      boundary: "Asset coverage hint only; not asset ranking",
    },
    {
      check: "Selected Source",
      status: sourceRows.length ? "Source rows loaded" : "Source empty",
      statusTone: sourceRows.length ? "positive" : "warning",
      evidence:
        selection.source === "all"
          ? `${formatRows(sourceRows.length)} rows across all sources`
          : `${formatRows(sourceRows.length)} rows for ${selection.symbol} / ${sourceLabel}`,
      nextAction: sourceRows.length ? "Use source for chart QA" : "Switch source or wait for provider sync",
      boundary: "Source coverage hint only; not provider ranking",
    },
    {
      check: "Chart Points",
      status: historyControlStatus(selectedRows.length).label,
      statusTone: historyControlStatus(selectedRows.length).tone,
      evidence: `${formatRows(selectedRows.length)} rows selected for visible history`,
      nextAction: selectedRows.length > 1 ? "Render and review line chart" : "Collect enough observations for a line",
      boundary: "Chart readiness only; not strategy signal",
    },
    {
      check: "Numeric Rates",
      status: numericRates.length ? "Rates parsed" : "No numeric rates",
      statusTone: numericRates.length ? "neutral" : "warning",
      evidence: `${formatRows(numericRates.length)} numeric rates in selected series`,
      nextAction: numericRates.length ? "Compare with diagnostics range" : "Verify provider rate mapping",
      boundary: "Rate parsing QA only; no carry bps or route cost bps",
    },
    {
      check: "Chart Empty State",
      status: chartState.label,
      statusTone: chartState.tone,
      evidence: chartState.evidence,
      nextAction: chartState.nextAction,
      boundary: "Empty-state explanation only; not a product signal",
    },
  ];
}

function buildFundingReleaseChecklist(
  rows: DataFundingRow[],
  health: DataHealthPayload | null,
  selectedHistoryRows: DataFundingRow[]
): FundingReleaseChecklistRow[] {
  const totalRows = rows.length;
  const okxRows = rows.filter((row) => row.exchange.toLowerCase() === "okx").length;
  const coinglassRows = rows.filter((row) => row.exchange.toLowerCase() === "coinglass").length;
  const qualityScore = health?.data_quality?.score ?? 0;
  const healthReady = health !== null;
  const hasBothSources = okxRows > 0 && coinglassRows > 0;
  const historyReady = selectedHistoryRows.length > 1;

  return [
    {
      area: "Data Health",
      status: healthReady ? "Health loaded" : "Health missing",
      statusTone: healthReady ? "positive" : "warning",
      evidence: healthReady ? `Data quality ${qualityScore.toFixed(0)}/100` : "No /data/health payload available",
      nextAction: healthReady ? "Keep health endpoint in release smoke" : "Check backend /data/health before release",
      boundary: "Release readiness only; not trading or execution signal",
    },
    {
      area: "Funding Rows",
      status: totalRows > 0 ? "Rows loaded" : "No rows",
      statusTone: totalRows > 0 ? "positive" : "warning",
      evidence: `${formatRows(totalRows)} rows across OKX/CoinGlass funding sources`,
      nextAction: totalRows > 0 ? "Keep MIN_TOTAL_ROWS guard enabled for preview/prod" : "Run funding sync before release smoke",
      boundary: "Data availability guard only; not strategy signal",
    },
    {
      area: "Source Coverage",
      status: hasBothSources ? "Both sources loaded" : "Partial source coverage",
      statusTone: hasBothSources ? "positive" : "warning",
      evidence: `OKX ${formatRows(okxRows)} rows / CoinGlass ${formatRows(coinglassRows)} rows`,
      nextAction: hasBothSources ? "Compare source QA before rollout" : "Inspect missing source before release",
      boundary: "Coverage readiness only; not provider ranking",
    },
    {
      area: "History Workflow",
      status: historyReady ? "History visible" : "History thin",
      statusTone: historyReady ? "positive" : "warning",
      evidence: `${formatRows(selectedHistoryRows.length)} rows selected for current history chart`,
      nextAction: historyReady ? "Review history diagnostics and readiness panels" : "Collect enough history for chart QA",
      boundary: "History release QA only; not carry or route input",
    },
    {
      area: "Panel Contract",
      status: "Panel ids tracked",
      statusTone: "positive",
      evidence: "Smoke checks source, anomaly, drilldown, history diagnostics, controls and readiness panels",
      nextAction: "Keep frontend marker check enabled for preview",
      boundary: "UI contract only; not production signal",
    },
    {
      area: "Compare Smoke",
      status: "Compare ready",
      statusTone: "neutral",
      evidence: "COMPARE_BASE_URL emits aligned/diff_detected/compare_failures summary",
      nextAction: "Run preview/prod compare with FAIL_ON_DIFF=1 before release",
      boundary: "Release drift check only; not trading or routing gate",
    },
    {
      area: "Safety Boundary",
      status: "Read-only locked",
      statusTone: "positive",
      evidence: "Smoke safety flags keep trading, execution, ranking, route selection and numeric cost outputs disabled",
      nextAction: "Do not enable forbidden outputs without product decision",
      boundary: "Safety boundary only; no execution path",
    },
    {
      area: "Release Decision",
      status: healthReady && totalRows > 0 ? "Ready for preview smoke" : "Needs data before release",
      statusTone: healthReady && totalRows > 0 ? "positive" : "warning",
      evidence: healthReady && totalRows > 0 ? "Health and funding rows are present" : "Health or funding rows are missing",
      nextAction:
        healthReady && totalRows > 0
          ? "Run release smoke and compare preview/prod"
          : "Populate rows and rerun funding QA smoke",
      boundary: "Release checklist only; not market recommendation",
    },
  ];
}

function buildFundingDataQualityRunway(
  rows: DataFundingRow[],
  health: DataHealthPayload | null,
  selectedHistoryRows: DataFundingRow[]
): FundingDataQualityRunwayRow[] {
  const totalRows = rows.length;
  const rowsBySource = FUNDING_EXCHANGES.reduce<Record<FundingExchange, number>>(
    (summary, exchange) => ({
      ...summary,
      [exchange]: rows.filter((row) => row.exchange.toLowerCase() === exchange).length,
    }),
    { okx: 0, coinglass: 0 }
  );
  const missingSources = FUNDING_EXCHANGES.filter((exchange) => rowsBySource[exchange] === 0).map(venueLabel);
  const fundingFreshnessRows =
    health?.freshness?.streams?.filter((row) => row.stream === "funding_rates") ?? [];
  const fundingCoverageRows = health?.coverage?.rows?.filter((row) => row.stream === "funding_rates") ?? [];
  const freshness = summarizeStatuses(fundingFreshnessRows, "Freshness not tracked");
  const coverage = summarizeStatuses(fundingCoverageRows, "Coverage not tracked");
  const syncRows = FUNDING_EXCHANGES.map((exchange) => fundingSyncHealth(health, exchange)).filter(
    (row): row is SyncTypeHealth => row !== null
  );
  const syncTone = syncRows.length ? worstTone(syncRows.map((row) => statusTone(row.status))) : "neutral";
  const syncEvidence = syncRows.length
    ? syncRows.map((row) => `${venueLabel(row.provider_name)} ${row.status}`).join(" / ")
    : "Sync health not tracked";
  const qualityScore = health?.data_quality?.score ?? 0;
  const qualityTone = health === null ? "warning" : qualityScore >= 80 ? "positive" : "warning";
  const historyReady = selectedHistoryRows.length > 1;
  const readyForPreview = health !== null && totalRows > 0 && missingSources.length === 0 && historyReady;

  return [
    {
      gate: "Data Health",
      status: health !== null ? "Health payload loaded" : "Health missing",
      statusTone: health !== null ? qualityTone : "warning",
      evidence: health !== null ? `Data quality ${qualityScore.toFixed(0)}/100` : "No /data/health payload",
      blocker: health !== null ? "None" : "Backend health evidence is missing",
      nextAction: health !== null ? "Keep /data/health in smoke evidence" : "Fix health endpoint before preview smoke",
      boundary: "Read-only QA gate; no trading, routing or execution signal",
    },
    {
      gate: "Funding Rows",
      status: totalRows > 0 ? "Rows present" : "Rows missing",
      statusTone: totalRows > 0 ? "positive" : "warning",
      evidence: `OKX ${formatRows(rowsBySource.okx)} / CoinGlass ${formatRows(rowsBySource.coinglass)}`,
      blocker: totalRows > 0 ? "None" : "No persisted funding rows",
      nextAction: totalRows > 0 ? "Keep MIN_TOTAL_ROWS guard enabled" : "Run funding sync before QA smoke",
      boundary: "Availability gate only; not a strategy signal",
    },
    {
      gate: "Source Coverage",
      status: missingSources.length === 0 ? "Sources covered" : "Partial sources",
      statusTone: missingSources.length === 0 ? "positive" : "warning",
      evidence:
        missingSources.length === 0
          ? "OKX and CoinGlass rows are present"
          : `Missing rows: ${missingSources.join(", ")}`,
      blocker: missingSources.length === 0 ? "None" : "Source rows are incomplete",
      nextAction: missingSources.length === 0 ? "Run provider comparison QA" : "Inspect source sync and mapping",
      boundary: "Coverage gate only; not provider ranking",
    },
    {
      gate: "Freshness & Coverage",
      status: worstTone([freshness.tone, coverage.tone, syncTone]) === "positive" ? "Tracked" : "Needs review",
      statusTone: worstTone([freshness.tone, coverage.tone, syncTone]),
      evidence: `${freshness.label}; ${coverage.label}; ${syncEvidence}`,
      blocker: worstTone([freshness.tone, coverage.tone, syncTone]) === "negative" ? "Health status degraded" : "None",
      nextAction: "Review source status and anomaly panels before release",
      boundary: "Data QA only; not market recommendation",
    },
    {
      gate: "History Preview",
      status: historyReady ? "Chart-ready rows selected" : "History thin",
      statusTone: historyReady ? "positive" : "warning",
      evidence: `${formatRows(selectedHistoryRows.length)} selected history rows`,
      blocker: historyReady ? "None" : "Selected history line may render empty",
      nextAction: historyReady ? "Capture preview evidence" : "Collect enough observations or use fallback source",
      boundary: "Chart readiness only; not strategy signal",
    },
    {
      gate: "v1.5.0 Preview Gate",
      status: readyForPreview ? "Ready for preview smoke" : "Needs QA evidence",
      statusTone: readyForPreview ? "positive" : "warning",
      evidence: readyForPreview
        ? "Health, source rows and history preview are present"
        : "One or more read-only QA gates need evidence",
      blocker: readyForPreview ? "None" : "Do not promote without smoke evidence",
      nextAction: readyForPreview ? "Run preview/prod compare smoke" : "Close blockers and rerun smoke",
      boundary: "Release gate only; no execution path",
    },
  ];
}

function sourcePairStatus(okxRate: number | null, coinglassRate: number | null): { label: string; tone: StatusTone } {
  if (okxRate === null && coinglassRate === null) return { label: "No source pair", tone: "warning" };
  if (okxRate === null) return { label: "Missing OKX side", tone: "warning" };
  if (coinglassRate === null) return { label: "Missing CoinGlass side", tone: "warning" };

  const difference = Math.abs(okxRate - coinglassRate);
  if (difference <= 0.005) return { label: "Aligned sources", tone: "positive" };
  if (difference <= 0.02) return { label: "Elevated source difference", tone: "warning" };
  return { label: "Divergent source difference", tone: "warning" };
}

function sourcePairDataNote(okxRow: DataFundingRow | null, coinglassRow: DataFundingRow | null): {
  label: string;
  tone: StatusTone;
} {
  if (okxRow && coinglassRow) return { label: "Both sources loaded", tone: "positive" };
  if (okxRow) return { label: "OKX only", tone: "warning" };
  if (coinglassRow) return { label: "CoinGlass only", tone: "warning" };
  return { label: "No funding rows", tone: "warning" };
}

function coverageLabel(row: CoverageRowSnapshot | null): string {
  if (!row) return "Not tracked";
  const expected = row.expected_rows === null ? "n/a" : formatRows(row.expected_rows);
  return `${row.status} / ${formatRows(row.rows)}/${expected}`;
}

function freshnessLabel(row: FreshnessStreamSnapshot | null, latest: number | null): string {
  if (row) return `${row.status} / ${formatAgeMinutes(row.age_minutes)} age`;
  if (latest !== null) return `Loaded / ${formatLatestAge(latest)}`;
  return "No loaded rows";
}

function syncLabel(row: SyncTypeHealth | null): string {
  if (!row) return "Sync not tracked";
  return `${row.status} / ${formatAgeMinutes(row.last_run_age_minutes)} ago`;
}

function fundingQaNextAction(
  loadedRows: number,
  freshness: FreshnessStreamSnapshot | null,
  coverage: CoverageRowSnapshot | null,
  sync: SyncTypeHealth | null
): string {
  if (loadedRows === 0) return "Run sync or verify provider mapping";
  if (sync && ["degraded", "stale"].includes(sync.status)) return "Inspect latest provider sync run";
  if (freshness && ["degraded", "stale"].includes(freshness.status)) return "Inspect freshness SLA and sync age";
  if (coverage && ["missing", "partial"].includes(coverage.status)) return "Backfill or observe funding window";
  return "Monitor; no data action required";
}

function buildFundingQaDrilldown(rows: DataFundingRow[], health: DataHealthPayload | null): FundingQaDrilldownRow[] {
  return WATCHED_SYMBOLS.flatMap((symbol) =>
    FUNDING_EXCHANGES.map((exchange) => {
      const sourceRows = rows.filter(
        (row) => row.symbol.toUpperCase() === symbol && row.exchange.toLowerCase() === exchange
      );
      const latest = latestTimestamp(sourceRows);
      const freshness = fundingFreshnessRow(health, symbol, exchange);
      const coverage = fundingCoverageRow(health, symbol, exchange);
      const sync = fundingSyncHealth(health, exchange);

      return {
        asset: symbol,
        source: venueLabel(exchange),
        loadedRows: formatRows(sourceRows.length),
        rowLatest: formatLatestAge(latest),
        freshness: freshnessLabel(freshness, latest),
        freshnessTone: statusTone(freshness?.status ?? (latest !== null ? "loaded" : "missing")),
        freshnessReason: freshness?.reason ?? "No freshness SLA row for this source",
        coverage: coverageLabel(coverage),
        coverageTone: statusTone(coverage?.status),
        coverageReason: coverage?.reason ?? "No coverage row for this source",
        sync: syncLabel(sync),
        syncTone: statusTone(sync?.status),
        nextAction: fundingQaNextAction(sourceRows.length, freshness, coverage, sync),
        boundary: "QA drilldown only; not carry, route ranking or execution signal",
      };
    })
  );
}

function buildFundingSourceComparisons(rows: DataFundingRow[]): FundingSourceComparisonRow[] {
  return WATCHED_SYMBOLS.map((symbol) => {
    const okxRow = latestFundingRow(rows, symbol, "okx");
    const coinglassRow = latestFundingRow(rows, symbol, "coinglass");
    const okxRate = okxRow ? rowRatePercent(okxRow) : null;
    const coinglassRate = coinglassRow ? rowRatePercent(coinglassRow) : null;
    const status = sourcePairStatus(okxRate, coinglassRate);
    const dataNote = sourcePairDataNote(okxRow, coinglassRow);
    const delta = okxRate !== null && coinglassRate !== null ? okxRate - coinglassRate : null;

    return {
      asset: symbol,
      okxRate: formatRateOrEmpty(okxRate),
      coinglassRate: formatRateOrEmpty(coinglassRate),
      sourceDelta: formatRateOrEmpty(delta),
      latestPair: `OKX ${formatLatestAge(okxRow?.timestamp ?? null)} / CoinGlass ${formatLatestAge(
        coinglassRow?.timestamp ?? null
      )}`,
      status: status.label,
      statusTone: status.tone,
      dataNote: dataNote.label,
      dataTone: dataNote.tone,
      boundary: "Provider comparison QA only; not route ranking, carry or execution signal",
    };
  });
}

function buildFundingFreshnessAnomalies(
  rows: DataFundingRow[],
  health: DataHealthPayload | null
): FundingFreshnessAnomalyRow[] {
  return WATCHED_SYMBOLS.flatMap((symbol) =>
    FUNDING_EXCHANGES.map((exchange) => {
      const sourceRows = rows
        .filter((row) => row.symbol.toUpperCase() === symbol && row.exchange.toLowerCase() === exchange)
        .sort((left, right) => left.timestamp - right.timestamp);
      const latest = latestTimestamp(sourceRows);
      const numericRates = sourceRows
        .map((row) => rowRatePercent(row))
        .filter((value): value is number => value !== null && Number.isFinite(value));
      const latestRate = numericRates.length ? numericRates[numericRates.length - 1] : null;
      const previousRate = numericRates.length > 1 ? numericRates[numericRates.length - 2] : null;
      const lastChange = latestRate !== null && previousRate !== null ? latestRate - previousRate : null;
      const dataStatus = fundingDataStatus(health, symbol, exchange, latest);
      const anomaly = fundingAnomalyStatus(numericRates);

      return {
        asset: symbol,
        source: venueLabel(exchange),
        observations: formatRows(sourceRows.length),
        latest: formatLatestAge(latest),
        latestRate: formatRateOrEmpty(latestRate),
        lastChange: formatRateOrEmpty(lastChange),
        dataStatus: dataStatus.label,
        dataTone: dataStatus.tone,
        anomaly: anomaly.label,
        anomalyTone: anomaly.tone,
        boundary: "Statistical data QA only; not carry, route or execution signal",
      };
    })
  );
}

function fundingHistory(rows: DataFundingRow[]): FundingRate[] {
  return rows
    .slice()
    .sort((a, b) => a.timestamp - b.timestamp)
    .slice(-48)
    .map((row) => {
      const rate = rowRatePercent(row) ?? 0;
      return {
        time: row.timestamp,
        asset: row.symbol.toUpperCase(),
        market: `${row.symbol.toUpperCase()}-USD PERP`,
        venue: venueLabel(row.exchange),
        rate,
        annualized: rate * 3 * 365,
      };
    });
}

function liquidityScore(openInterestUsd?: number | null): number {
  if (!openInterestUsd || openInterestUsd <= 0) return 62;
  return Math.max(62, Math.min(95, Math.round(58 + Math.log10(openInterestUsd / 1_000_000) * 7)));
}

function syncSummary(
  health: DataHealthPayload | null,
  provider: string,
  syncType: string
): { label: string; tone: StatusTone } {
  const sync = health?.sync_health_by_type?.[provider]?.[syncType];
  if (!sync) return { label: "Sync not tracked", tone: "neutral" };

  const age = sync.last_run_age_minutes === null ? "unknown age" : `${formatAgeMinutes(sync.last_run_age_minutes)} ago`;
  return {
    label: `${sync.status} / ${age}`,
    tone: statusTone(sync.status),
  };
}

function fundingFreshnessSummary(
  health: DataHealthPayload | null,
  exchange: FundingExchange,
  latest: number | null
): { label: string; tone: StatusTone } {
  const rows =
    health?.freshness?.streams?.filter(
      (row) => row.stream === "funding_rates" && row.exchange.toLowerCase() === exchange
    ) ?? [];

  if (rows.length) {
    const status = summarizeStatuses(rows, "Not tracked");
    const ages = rows
      .map((row) => row.age_minutes)
      .filter((value): value is number => value !== null && value !== undefined && Number.isFinite(value));
    const maxAge = ages.length ? Math.max(...ages) : null;
    return {
      label: `${status.label}${maxAge !== null ? ` / max ${formatAgeMinutes(maxAge)}` : ""}`,
      tone: status.tone,
    };
  }

  if (latest !== null) {
    return { label: `Snapshot latest ${formatLatestAge(latest)}`, tone: "positive" };
  }

  return { label: "No loaded rows", tone: "warning" };
}

function fundingCoverageSummary(
  health: DataHealthPayload | null,
  exchange: FundingExchange,
  loadedRows: number
): { label: string; tone: StatusTone } {
  const rows =
    health?.coverage?.rows?.filter(
      (row) => row.stream === "funding_rates" && row.exchange.toLowerCase() === exchange
    ) ?? [];

  if (rows.length) return summarizeStatuses(rows, "Not tracked");
  if (exchange === "coinglass" && loadedRows > 0) {
    return { label: "Snapshot feed / no 7d SLA", tone: "neutral" };
  }
  return { label: "Not tracked", tone: "neutral" };
}

function buildFundingSourceStatus(rows: DataFundingRow[], health: DataHealthPayload | null): FundingSourceStatusRow[] {
  return FUNDING_EXCHANGES.map((exchange) => {
    const sourceRows = rows.filter((row) => row.exchange.toLowerCase() === exchange);
    const latest = latestTimestamp(sourceRows);
    const freshness = fundingFreshnessSummary(health, exchange, latest);
    const coverage = fundingCoverageSummary(health, exchange, sourceRows.length);
    const sync = syncSummary(health, exchange, exchange === "coinglass" ? "snapshots" : "funding_rates");

    return {
      source: exchange === "okx" ? "OKX funding history" : "CoinGlass funding snapshots",
      scope: exchange === "okx" ? "Primary 8h persisted history" : "Third-party snapshot enrichment",
      loadedRows: formatRows(sourceRows.length),
      latest: formatLatestAge(latest),
      freshness: freshness.label,
      freshnessTone: freshness.tone,
      coverage: coverage.label,
      coverageTone: coverage.tone,
      sync: sync.label,
      syncTone: sync.tone,
      boundary:
        exchange === "okx"
          ? "Read-only analytics; not execution-grade carry or route input"
          : "Research enrichment; not route ranking or execution signal",
    };
  });
}

function buildFundingData(
  rows: DataFundingRow[],
  health: DataHealthPayload | null,
  options?: FundingHistoryOptions
): LiveFundingOverview {
  const historySelection = normalizeHistorySelection(options);
  const latest = latestRows(rows);
  const current = latest
    .map((row) => {
      const rate = rowRatePercent(row);
      if (rate === null) return null;
      return {
        symbol: row.symbol.toUpperCase(),
        venue: venueLabel(row.exchange),
        exchange: row.exchange.toLowerCase(),
        rate,
        annualized: rate * 3 * 365,
        timestamp: row.timestamp,
      };
    })
    .filter((row): row is NonNullable<typeof row> => row !== null);

  const assets = Array.from(new Set([...WATCHED_SYMBOLS, ...current.map((row) => row.symbol)])).filter((symbol) =>
    current.some((row) => row.symbol === symbol)
  );
  const venues = FUNDING_EXCHANGES.map(venueLabel).filter((venue) =>
    current.some((row) => exchangeKey(row.venue) === exchangeKey(venue))
  );
  const currentByCell = new Map(current.map((row) => [`${row.symbol}:${exchangeKey(row.venue)}`, row.rate]));
  const rates = current.map((row) => row.rate);
  const avgRate = rates.length ? rates.reduce((sum, value) => sum + value, 0) / rates.length : 0;
  const topPositive = current.length ? current.reduce((best, row) => (row.rate > best.rate ? row : best), current[0]) : null;
  const topNegative = current.length ? current.reduce((best, row) => (row.rate < best.rate ? row : best), current[0]) : null;
  const rowCounts = health?.row_counts ?? {};
  const qualityScore = health?.data_quality?.score ?? 0;
  const fundingRows = rowCounts.funding_rates ?? 0;

  const matrix = assets.map((asset) =>
    venues.map((venue) => ({
      asset,
      venue,
      rate: currentByCell.get(`${asset}:${exchangeKey(venue)}`) ?? Number.NaN,
    }))
  );

  const { selectedRows: selectedHistoryRows, assetRows, sourceRows, fallbackUsed } = selectFundingHistoryRows(
    rows,
    historySelection
  );
  const history = fundingHistory(selectedHistoryRows);
  const historyLabel = `${historySelection.symbol} / ${
    fallbackUsed ? "Fallback rows" : historySourceLabel(historySelection.source)
  }`;

  const sortedByAbsoluteRate = current.slice().sort((a, b) => Math.abs(b.rate) - Math.abs(a.rate));
  const arbitrage = sortedByAbsoluteRate.slice(0, 5).map((row) => {
    const score = liquidityScore(null);
    const receivesShort = row.rate >= 0;

    return {
      asset: row.symbol,
      longLeg: receivesShort ? "Spot hedge" : `${row.venue} perp`,
      shortLeg: receivesShort ? `${row.venue} perp` : "Spot hedge",
      fundingEdge: Math.abs(row.rate),
      netApr: Math.abs(row.annualized),
      liquidityScore: score,
      riskScore: Math.max(12, 100 - score),
    };
  });

  const longShortLegs = current.slice(0, 8).map((row) => ({
    asset: row.symbol,
    venue: row.venue,
    receiveSide: row.rate >= 0 ? ("short" as const) : ("long" as const),
    currentRate: row.rate,
    estimatedApr: Math.abs(row.annualized),
  }));

  const predicted = current.slice(0, 8).map((row) => ({
    time: row.timestamp,
    asset: row.symbol,
    market: `${row.symbol}-USD PERP`,
    venue: row.venue,
    rate: row.rate,
  }));

  const kpis: KpiMetric[] = [
    {
      label: "Avg Funding",
      value: current.length ? formatPercent(avgRate) : "No data",
      caption: current.length ? `${current.length} live DB points` : "PostgreSQL empty",
      tone: avgRate > 0 ? "positive" : avgRate < 0 ? "negative" : "warning",
      sparkline: history.length > 0 ? history.slice(-8).map((point) => point.rate) : undefined,
    },
    {
      label: "Top Positive",
      value: topPositive ? formatPercent(topPositive.rate) : "No data",
      caption: topPositive ? `${topPositive.symbol} / ${topPositive.venue}` : undefined,
      tone: topPositive && topPositive.rate > 0 ? "positive" : "neutral",
    },
    {
      label: "Top Negative",
      value: topNegative ? formatPercent(topNegative.rate) : "No data",
      caption: topNegative ? `${topNegative.symbol} / ${topNegative.venue}` : undefined,
      tone: topNegative && topNegative.rate < 0 ? "negative" : "neutral",
    },
    {
      label: "Funding Regime",
      value: avgRate > 0 ? "Positive" : avgRate < 0 ? "Negative" : "Neutral",
      caption: avgRate > 0 ? "Shorts receive" : avgRate < 0 ? "Longs receive" : "Flat",
      tone: avgRate > 0 ? "positive" : avgRate < 0 ? "negative" : "neutral",
    },
    {
      label: "DB Funding Rows",
      value: formatRows(fundingRows),
      caption: "PostgreSQL",
      tone: fundingRows > 0 ? "positive" : "warning",
    },
    {
      label: "Data Quality",
      value: `${qualityScore.toFixed(0)}/100`,
      caption: `${health?.data_quality?.window_hours ?? 24}h window`,
      tone: qualityScore >= 80 ? "positive" : qualityScore > 0 ? "warning" : "negative",
    },
  ];

  const data: FundingData = {
    kpis,
    venues,
    assets,
    dataQualityRunway: buildFundingDataQualityRunway(rows, health, selectedHistoryRows),
    releaseChecklist: buildFundingReleaseChecklist(rows, health, selectedHistoryRows),
    sourceStatus: buildFundingSourceStatus(rows, health),
    freshnessAnomalies: buildFundingFreshnessAnomalies(rows, health),
    sourceComparisons: buildFundingSourceComparisons(rows),
    qaDrilldown: buildFundingQaDrilldown(rows, health),
    anomalyDetails: buildFundingAnomalyDetails(rows),
    historyDiagnostics: buildFundingHistoryDiagnostics(rows, health),
    historyControls: buildFundingHistoryControls(
      historySelection,
      selectedHistoryRows,
      assetRows,
      sourceRows,
      fallbackUsed
    ),
    historyReadiness: buildFundingHistoryReadiness(
      historySelection,
      rows,
      selectedHistoryRows,
      assetRows,
      sourceRows,
      fallbackUsed
    ),
    matrix,
    history,
    arbitrage,
    longShortLegs,
    predicted,
  };

  if (current.length) {
    return {
      data,
      statusLabel: "Live PostgreSQL data",
      statusTone: "positive",
      sourceCaption: "Persisted OKX and CoinGlass funding rows from PostgreSQL.",
      historyLabel,
      historySelection: {
        asset: historySelection.symbol,
        source: historySelection.source,
      },
    };
  }

  return {
    data,
    statusLabel: "No funding rows",
    statusTone: "warning",
    sourceCaption: "Run market data sync to populate PostgreSQL funding tables.",
    historyLabel,
    historySelection: {
      asset: historySelection.symbol,
      source: historySelection.source,
    },
  };
}

export async function getLiveFundingOverview(options?: FundingHistoryOptions): Promise<LiveFundingOverview> {
  const requests = FUNDING_EXCHANGES.flatMap((exchange) =>
    WATCHED_SYMBOLS.map((symbol) => ({
      symbol,
      exchange,
      path: `/data/funding?symbol=${symbol}&exchange=${exchange}`,
    }))
  );

  const [healthResponse, ...fundingResponses] = await Promise.all([
    fetchServerApi<DataHealthPayload>("/data/health"),
    ...requests.map((request) => fetchServerApi<DataFundingRow[]>(request.path)),
  ]);

  const rows = fundingResponses.flatMap((response) => (response?.success ? response.data : []));

  return buildFundingData(rows, healthResponse?.success ? healthResponse.data : null, options);
}

export async function getLiveDataHealth(): Promise<DataHealthPayload | null> {
  const response = await fetchServerApi<DataHealthPayload>("/data/health");
  return response?.success ? response.data : null;
}
