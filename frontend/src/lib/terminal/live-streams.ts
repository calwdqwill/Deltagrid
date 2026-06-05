import { fetchServerApi } from "@/lib/server-api";
import { KpiMetric, SeriesPoint } from "@/types/terminal";
import { DataHealthPayload } from "./live-data";

const TRACKED_SYMBOLS = ["BTC", "ETH", "SOL"] as const;
const DEFAULT_EXCHANGE = "binance";

type StatusTone = "positive" | "warning";

interface OhlcvRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  interval: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume?: number | null;
  quote_volume?: number | null;
}

interface FundingRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  funding_rate: number | string | null;
  interval?: string | null;
}

interface OpenInterestRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  interval: string;
  oi_usd?: number | null;
  oi_coins?: number | null;
}

interface LongShortRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  interval: string;
  long_ratio?: number | null;
  short_ratio?: number | null;
  long_account_ratio?: number | null;
  short_account_ratio?: number | null;
}

interface BasisPremiumRow {
  id: string;
  timestamp: number;
  symbol: string;
  exchange: string;
  spot_price?: number | null;
  perp_price?: number | null;
  basis_pct?: number | null;
  premium_pct?: number | null;
}

interface LiquidationRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  side: string;
  quantity?: number | null;
  price?: number | null;
  value_usd?: number | null;
}

export interface LiveChartsWorkspace {
  symbol: string;
  statusLabel: string;
  statusTone: StatusTone;
  kpis: KpiMetric[];
  priceSeries: SeriesPoint[];
  volumeSeries: SeriesPoint[];
  openInterestSeries: SeriesPoint[];
  basisSeries: SeriesPoint[];
  fundingSeries: SeriesPoint[];
  longRatioSeries: SeriesPoint[];
  sourceRows: Array<[string, string, string]>;
}

export interface LiveMatrixRow {
  asset: string;
  spotPrice: number | null;
  perpPrice: number | null;
  basisPct: number | null;
  fundingPct: number | null;
  openInterestUsd: number | null;
  longAccountRatio: number | null;
}

export interface LiveMarketMatrix {
  rows: LiveMatrixRow[];
  kpis: KpiMetric[];
  statusLabel: string;
  statusTone: StatusTone;
  sourceRows: Array<[string, string]>;
}

export interface LiveArbitrageOpportunity {
  id: string;
  type: "basis" | "funding_bias";
  asset: string;
  longLeg: string;
  shortLeg: string;
  edgePct: number;
  fundingPct: number | null;
  openInterestUsd: number | null;
  source: string;
  riskNote: string;
}

export interface LiveArbitrageScanner {
  opportunities: LiveArbitrageOpportunity[];
  kpis: KpiMetric[];
  statusLabel: string;
  statusTone: StatusTone;
}

export interface LiveStrategyReadiness {
  kpis: KpiMetric[];
  priceSeries: SeriesPoint[];
  fundingSeries: SeriesPoint[];
  readinessRows: Array<[string, string, string]>;
  statusLabel: string;
  statusTone: StatusTone;
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function latest<T extends { timestamp: number }>(rows: T[]): T | null {
  if (!rows.length) return null;
  return rows.reduce((best, row) => (row.timestamp > best.timestamp ? row : best), rows[0]);
}

function formatRows(value?: number): string {
  return (value ?? 0).toLocaleString("en-US");
}

function formatCompactCurrency(value: number | null): string {
  if (value === null) return "No data";
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (abs >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

function formatPercent(value: number | null, digits = 3): string {
  if (value === null) return "No data";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

function pointLabel(timestamp: number): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return String(timestamp);
  return date.toISOString().slice(11, 16);
}

function rowsToSeries<T extends { timestamp: number }>(
  rows: T[],
  valueSelector: (row: T) => number | null,
  maxPoints = 96
): SeriesPoint[] {
  return rows
    .slice(-maxPoints)
    .map((row) => ({ label: pointLabel(row.timestamp), value: valueSelector(row) }))
    .filter((point): point is SeriesPoint => point.value !== null);
}

function fundingPercent(row: FundingRow | null): number | null {
  const rate = toNumber(row?.funding_rate);
  return rate === null ? null : rate * 100;
}

function longAccountPercent(row: LongShortRow | null): number | null {
  const direct = toNumber(row?.long_account_ratio);
  if (direct !== null) return direct * 100;
  const fallback = toNumber(row?.long_ratio);
  return fallback === null ? null : fallback * 100;
}

async function fetchRows<T>(path: string): Promise<T[]> {
  const response = await fetchServerApi<T[]>(path);
  return response?.success ? response.data : [];
}

async function symbolStreams(symbol: string) {
  const normalizedSymbol = symbol.toUpperCase();
  const [ohlcv, funding, oiBinance, oiCoinGlass, basis, longShort, liquidations] = await Promise.all([
    fetchRows<OhlcvRow>(`/data/ohlcv?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}&interval=1m`),
    fetchRows<FundingRow>(`/data/funding?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`),
    fetchRows<OpenInterestRow>(`/data/open-interest?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`),
    fetchRows<OpenInterestRow>(`/data/open-interest?symbol=${normalizedSymbol}&exchange=coinglass`),
    fetchRows<BasisPremiumRow>(`/data/basis-premium?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`),
    fetchRows<LongShortRow>(`/data/long-short-ratio?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`),
    fetchRows<LiquidationRow>(`/data/liquidations?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`),
  ]);

  return {
    symbol: normalizedSymbol,
    ohlcv,
    funding,
    openInterest: oiCoinGlass.length ? oiCoinGlass : oiBinance,
    basis,
    longShort,
    liquidations,
  };
}

export async function getLiveChartsWorkspace(symbol = "BTC"): Promise<LiveChartsWorkspace> {
  const streams = await symbolStreams(symbol);
  const healthResponse = await fetchServerApi<DataHealthPayload>("/data/health");
  const health = healthResponse?.success ? healthResponse.data : null;
  const latestCandle = latest(streams.ohlcv);
  const latestFunding = latest(streams.funding);
  const latestOi = latest(streams.openInterest);
  const latestBasis = latest(streams.basis);
  const latestLongShort = latest(streams.longShort);
  const price = toNumber(latestCandle?.close);
  const funding = fundingPercent(latestFunding);
  const oiUsd = toNumber(latestOi?.oi_usd);
  const basisPct = toNumber(latestBasis?.basis_pct);
  const longPct = longAccountPercent(latestLongShort);
  const rowCounts = health?.row_counts ?? {};

  const kpis: KpiMetric[] = [
    {
      label: "Last Price",
      value: price === null ? "No data" : `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`,
      caption: `${streams.symbol} Binance 1m`,
      tone: price !== null ? "positive" : "warning",
    },
    {
      label: "Funding",
      value: formatPercent(funding),
      caption: "Binance history",
      tone: funding === null ? "warning" : funding >= 0 ? "positive" : "negative",
    },
    {
      label: "Open Interest",
      value: formatCompactCurrency(oiUsd),
      caption: latestOi?.exchange ?? "No OI rows",
      tone: oiUsd !== null && oiUsd > 0 ? "positive" : "warning",
    },
    {
      label: "Basis",
      value: formatPercent(basisPct),
      caption: "CoinGecko spot vs Binance perp",
      tone: basisPct === null ? "warning" : basisPct >= 0 ? "positive" : "negative",
    },
    {
      label: "Long Accounts",
      value: formatPercent(longPct, 2),
      caption: "Binance L/S",
      tone: longPct === null ? "warning" : longPct >= 50 ? "positive" : "negative",
    },
    {
      label: "Data Rows",
      value: formatRows(rowCounts.ohlcv),
      caption: "OHLCV in PostgreSQL",
      tone: (rowCounts.ohlcv ?? 0) > 0 ? "positive" : "warning",
    },
  ];

  return {
    symbol: streams.symbol,
    statusLabel: streams.ohlcv.length ? "Live PostgreSQL streams" : "No OHLCV rows",
    statusTone: streams.ohlcv.length ? "positive" : "warning",
    kpis,
    priceSeries: rowsToSeries(streams.ohlcv, (row) => toNumber(row.close)),
    volumeSeries: rowsToSeries(streams.ohlcv, (row) => toNumber(row.quote_volume) ?? toNumber(row.volume)),
    openInterestSeries: rowsToSeries(streams.openInterest, (row) => toNumber(row.oi_usd)),
    basisSeries: rowsToSeries(streams.basis, (row) => toNumber(row.basis_pct)),
    fundingSeries: rowsToSeries(streams.funding, fundingPercent),
    longRatioSeries: rowsToSeries(streams.longShort, (row) => longAccountPercent(row)),
    sourceRows: [
      ["OHLCV", `${streams.ohlcv.length} rows`, "Binance 1m"],
      ["Funding", `${streams.funding.length} rows`, "Binance"],
      ["Open Interest", `${streams.openInterest.length} rows`, latestOi?.exchange ?? "binance/coinglass"],
      ["Basis", `${streams.basis.length} rows`, "CoinGecko + Binance"],
      ["Long/Short", `${streams.longShort.length} rows`, "Binance"],
      ["Liquidations", `${streams.liquidations.length} rows`, "Pending ingestion when 0"],
    ],
  };
}

export async function getLiveMarketMatrix(): Promise<LiveMarketMatrix> {
  const [btc, eth, sol, healthResponse] = await Promise.all([
    symbolStreams("BTC"),
    symbolStreams("ETH"),
    symbolStreams("SOL"),
    fetchServerApi<DataHealthPayload>("/data/health"),
  ]);
  const streams = [btc, eth, sol];
  const health = healthResponse?.success ? healthResponse.data : null;

  const rows: LiveMatrixRow[] = streams.map((stream) => {
    const candle = latest(stream.ohlcv);
    const basis = latest(stream.basis);
    const funding = latest(stream.funding);
    const oi = latest(stream.openInterest);
    const longShort = latest(stream.longShort);

    return {
      asset: stream.symbol,
      spotPrice: toNumber(basis?.spot_price),
      perpPrice: toNumber(basis?.perp_price) ?? toNumber(candle?.close),
      basisPct: toNumber(basis?.basis_pct),
      fundingPct: fundingPercent(funding),
      openInterestUsd: toNumber(oi?.oi_usd),
      longAccountRatio: longAccountPercent(longShort),
    };
  });
  const liveRows = rows.filter((row) => row.perpPrice !== null || row.spotPrice !== null).length;
  const maxBasis = rows.reduce<LiveMatrixRow | null>((best, row) => {
    if (row.basisPct === null) return best;
    if (!best || Math.abs(row.basisPct) > Math.abs(best.basisPct ?? 0)) return row;
    return best;
  }, null);
  const maxOi = rows.reduce<LiveMatrixRow | null>((best, row) => {
    if (row.openInterestUsd === null) return best;
    if (!best || row.openInterestUsd > (best.openInterestUsd ?? 0)) return row;
    return best;
  }, null);

  return {
    rows,
    statusLabel: liveRows ? "Live PostgreSQL matrix" : "No matrix rows",
    statusTone: liveRows ? "positive" : "warning",
    kpis: [
      {
        label: "Assets",
        value: `${liveRows}/${rows.length}`,
        caption: "BTC/ETH/SOL",
        tone: liveRows === rows.length ? "positive" : "warning",
      },
      {
        label: "Max Basis",
        value: maxBasis ? `${maxBasis.asset} ${formatPercent(maxBasis.basisPct)}` : "No data",
        caption: "Spot vs perp",
        tone: maxBasis?.basisPct === undefined || maxBasis?.basisPct === null ? "warning" : maxBasis.basisPct >= 0 ? "positive" : "negative",
      },
      {
        label: "Largest OI",
        value: maxOi ? maxOi.asset : "No data",
        caption: maxOi ? formatCompactCurrency(maxOi.openInterestUsd) : "Open interest",
        tone: maxOi ? "positive" : "warning",
      },
      {
        label: "Funding Rows",
        value: formatRows(health?.row_counts.funding_rates),
        caption: "PostgreSQL",
        tone: (health?.row_counts.funding_rates ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "OI Rows",
        value: formatRows(health?.row_counts.open_interest),
        caption: "PostgreSQL",
        tone: (health?.row_counts.open_interest ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Basis Rows",
        value: formatRows(health?.row_counts.basis_premium),
        caption: "PostgreSQL",
        tone: (health?.row_counts.basis_premium ?? 0) > 0 ? "positive" : "warning",
      },
    ],
    sourceRows: [
      ["Price", "CoinGecko spot + latest Binance 1m perp close"],
      ["Funding", "Binance funding history"],
      ["Open Interest", "CoinGlass snapshot preferred, Binance fallback"],
      ["Basis", "CoinGecko spot vs Binance perp approximate snapshot"],
      ["Long/Short", "Binance account ratio"],
    ],
  };
}

export async function getLiveArbitrageScanner(): Promise<LiveArbitrageScanner> {
  const matrix = await getLiveMarketMatrix();
  const opportunities: LiveArbitrageOpportunity[] = matrix.rows
    .filter((row) => row.basisPct !== null || row.fundingPct !== null)
    .map((row) => {
      const basis = row.basisPct ?? 0;
      const funding = row.fundingPct ?? 0;
      const edge = Math.abs(basis);
      const shortPerp = basis >= 0;
      const type: LiveArbitrageOpportunity["type"] = edge >= Math.abs(funding) ? "basis" : "funding_bias";

      return {
        id: `basis-${row.asset.toLowerCase()}`,
        type,
        asset: row.asset,
        longLeg: shortPerp ? "CoinGecko spot proxy" : "Binance perp",
        shortLeg: shortPerp ? "Binance perp" : "CoinGecko spot proxy",
        edgePct: edge,
        fundingPct: row.fundingPct,
        openInterestUsd: row.openInterestUsd,
        source: "basis_premium + funding_rates",
        riskNote: row.openInterestUsd && row.openInterestUsd > 0 ? "Data-backed" : "OI missing",
      };
    })
    .sort((left, right) => right.edgePct - left.edgePct);

  return {
    opportunities,
    statusLabel: opportunities.length ? "Live basis scan" : "No live opportunities",
    statusTone: opportunities.length ? "positive" : "warning",
    kpis: [
      {
        label: "Opportunities",
        value: String(opportunities.length),
        caption: "Basis/funding candidates",
        tone: opportunities.length ? "positive" : "warning",
      },
      {
        label: "Largest Edge",
        value: opportunities[0] ? `${opportunities[0].asset} ${formatPercent(opportunities[0].edgePct)}` : "No data",
        caption: "Absolute basis",
        tone: opportunities[0] ? "positive" : "warning",
      },
      ...matrix.kpis.slice(3, 6),
    ],
  };
}

export async function getLiveStrategyReadiness(): Promise<LiveStrategyReadiness> {
  const [charts, healthResponse] = await Promise.all([
    getLiveChartsWorkspace("BTC"),
    fetchServerApi<DataHealthPayload>("/data/health"),
  ]);
  const health = healthResponse?.success ? healthResponse.data : null;
  const rows = health?.row_counts ?? {};
  const hasCoreInputs = (rows.ohlcv ?? 0) > 0 && (rows.funding_rates ?? 0) > 0 && (rows.open_interest ?? 0) > 0;

  return {
    statusLabel: hasCoreInputs ? "Live inputs ready" : "Inputs incomplete",
    statusTone: hasCoreInputs ? "positive" : "warning",
    priceSeries: charts.priceSeries,
    fundingSeries: charts.fundingSeries,
    kpis: [
      {
        label: "Backtest Engine",
        value: "Pending",
        caption: "No fake run result",
        tone: "warning",
      },
      {
        label: "OHLCV Rows",
        value: formatRows(rows.ohlcv),
        caption: "Price input",
        tone: (rows.ohlcv ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Funding Rows",
        value: formatRows(rows.funding_rates),
        caption: "Funding input",
        tone: (rows.funding_rates ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "OI Rows",
        value: formatRows(rows.open_interest),
        caption: "Risk/liquidity input",
        tone: (rows.open_interest ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Basis Rows",
        value: formatRows(rows.basis_premium),
        caption: "Basis input",
        tone: (rows.basis_premium ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Data Quality",
        value: health ? `${health.data_quality.score.toFixed(0)}/100` : "No data",
        caption: "24h window",
        tone: health && health.data_quality.score >= 80 ? "positive" : "warning",
      },
    ],
    readinessRows: [
      ["Price candles", formatRows(rows.ohlcv), (rows.ohlcv ?? 0) > 0 ? "Ready" : "Missing"],
      ["Funding rates", formatRows(rows.funding_rates), (rows.funding_rates ?? 0) > 0 ? "Ready" : "Missing"],
      ["Open interest", formatRows(rows.open_interest), (rows.open_interest ?? 0) > 0 ? "Ready" : "Missing"],
      ["Basis snapshots", formatRows(rows.basis_premium), (rows.basis_premium ?? 0) > 0 ? "Ready" : "Missing"],
      ["Liquidations", formatRows(rows.liquidations), (rows.liquidations ?? 0) > 0 ? "Ready" : "Pending ingestion"],
      ["Backtest engine", "0 live runs", "Pending implementation"],
    ],
  };
}

export { TRACKED_SYMBOLS };
