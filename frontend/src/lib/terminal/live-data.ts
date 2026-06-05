import { fetchServerApi } from "@/lib/server-api";
import { FundingData, FundingRate, KpiMetric } from "@/types/terminal";

type StatusTone = "positive" | "negative" | "warning" | "neutral";

type FundingExchange = "binance" | "coinglass";

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
}

export interface LiveFundingOverview {
  data: FundingData;
  statusLabel: string;
  statusTone: StatusTone;
  sourceCaption: string;
  historyLabel: string;
}

const WATCHED_SYMBOLS = ["BTC", "ETH", "SOL"];
const FUNDING_EXCHANGES: FundingExchange[] = ["coinglass", "binance"];

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

function venueLabel(exchange: string): string {
  const normalized = exchange.toLowerCase();
  if (normalized === "coinglass") return "CoinGlass";
  if (normalized === "binance") return "Binance";
  return exchange;
}

function exchangeKey(venue: string): string {
  return venue.toLowerCase();
}

function rowRatePercent(row: DataFundingRow): number | null {
  const rate = toNumber(row.funding_rate);
  return rate === null ? null : rate * 100;
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

function buildFundingData(rows: DataFundingRow[], health: DataHealthPayload | null): LiveFundingOverview {
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

  const preferredHistoryRows =
    rows.filter((row) => row.symbol.toUpperCase() === "BTC" && row.exchange.toLowerCase() === "coinglass") ||
    [];
  const fallbackHistoryRows = preferredHistoryRows.length
    ? preferredHistoryRows
    : rows.filter((row) => row.symbol.toUpperCase() === "BTC");
  const selectedHistoryRows = fallbackHistoryRows.length ? fallbackHistoryRows : rows;
  const history = fundingHistory(selectedHistoryRows);
  const historyLabel = history[0] ? `${history[0].asset} · ${history[0].venue}` : "No funding history";

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
      caption: topPositive ? `${topPositive.symbol} · ${topPositive.venue}` : undefined,
      tone: topPositive && topPositive.rate > 0 ? "positive" : "neutral",
    },
    {
      label: "Top Negative",
      value: topNegative ? formatPercent(topNegative.rate) : "No data",
      caption: topNegative ? `${topNegative.symbol} · ${topNegative.venue}` : undefined,
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
      sourceCaption: "Funding rates are read from persisted provider sync rows.",
      historyLabel,
    };
  }

  return {
    data,
    statusLabel: "No funding rows",
    statusTone: "warning",
    sourceCaption: "Run market data sync to populate PostgreSQL funding tables.",
    historyLabel,
  };
}

export async function getLiveFundingOverview(): Promise<LiveFundingOverview> {
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

  return buildFundingData(rows, healthResponse?.success ? healthResponse.data : null);
}

export async function getLiveDataHealth(): Promise<DataHealthPayload | null> {
  const response = await fetchServerApi<DataHealthPayload>("/data/health");
  return response?.success ? response.data : null;
}
