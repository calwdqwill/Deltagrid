export type VenueType = "cex" | "perp_dex" | "dex";
export type MarketType = "spot" | "perp" | "futures";
export type OpportunityType = "basis" | "cross_exchange" | "liquidity" | "oi_divergence";

export interface Asset {
  id: string;
  symbol: string;
  name: string;
  image?: string | null;
  price: number;
  change24h: number;
  change7d: number;
  marketCap: number;
  volume24h: number;
  volumeToMarketCap: number;
  openInterest: number;
  perpVolume: number;
  sparkline: number[];
}

export interface Venue {
  id: string;
  name: string;
  type: VenueType;
  share: number;
  liquidityScore: number;
  openInterest: number;
  volume24h: number;
}

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface SeriesPoint {
  label: string;
  value: number;
}

export interface KpiMetric {
  label: string;
  value: string;
  delta?: string;
  tone?: "positive" | "negative" | "warning" | "neutral";
  sparkline?: number[];
  caption?: string;
}

export interface MarketHeatmapItem {
  symbol: string;
  name: string;
  image?: string | null;
  price: number;
  value: number;
  change24h: number;
  marketCap: number;
}

export interface MarketOverviewData {
  kpis: KpiMetric[];
  heatmap: MarketHeatmapItem[];
  btcOverview: AssetSnapshot;
  ethOverview: AssetSnapshot;
  marketBreadth: {
    advancing: number;
    neutral: number;
    declining: number;
    histogram: SeriesPoint[];
  };
  topGainers: RankedAssetMove[];
  topLosers: RankedAssetMove[];
  topAssets: Asset[];
}

export interface RankedAssetMove {
  rank: number;
  symbol: string;
  name: string;
  change24h: number;
}

export interface AssetSnapshot {
  symbol: string;
  name: string;
  image?: string | null;
  price: number;
  change24h: number;
  marketCap: number;
  volume24h: number;
  dominance?: number;
  sparkline: number[];
}

export interface PerpDexData {
  kpis: KpiMetric[];
  venues: Venue[];
  volumeShare: SeriesPoint[];
  oiShare: SeriesPoint[];
  stackedVolume: Array<{ time: string; values: Record<string, number> }>;
  liquidityMetrics: Array<{ venue: string; score: number }>;
  markets: PerpMarketRow[];
}

export interface PerpMarketRow {
  market: string;
  venue: string;
  price: number;
  volume24h: number;
  openInterest: number;
  liquidityScore: number;
  oiToVolume: number;
}

export interface FundingRate {
  time: number;
  asset: string;
  market: string;
  venue: string;
  rate: number;
  annualized?: number;
  predicted?: number;
}

export interface FundingData {
  kpis: KpiMetric[];
  venues: string[];
  assets: string[];
  releaseChecklist: FundingReleaseChecklistRow[];
  sourceStatus: FundingSourceStatusRow[];
  freshnessAnomalies: FundingFreshnessAnomalyRow[];
  sourceComparisons: FundingSourceComparisonRow[];
  qaDrilldown: FundingQaDrilldownRow[];
  anomalyDetails: FundingAnomalyDetailRow[];
  historyDiagnostics: FundingHistoryDiagnosticRow[];
  historyControls: FundingHistoryControlRow[];
  historyReadiness: FundingHistoryReadinessRow[];
  matrix: FundingMatrixCell[][];
  history: FundingRate[];
  arbitrage: FundingOpportunity[];
  longShortLegs: LongShortLeg[];
  predicted: FundingRate[];
}

export interface FundingSourceStatusRow {
  source: string;
  scope: string;
  loadedRows: string;
  latest: string;
  freshness: string;
  freshnessTone: "positive" | "negative" | "warning" | "neutral";
  coverage: string;
  coverageTone: "positive" | "negative" | "warning" | "neutral";
  sync: string;
  syncTone: "positive" | "negative" | "warning" | "neutral";
  boundary: string;
}

export interface FundingReleaseChecklistRow {
  area: string;
  status: string;
  statusTone: "positive" | "negative" | "warning" | "neutral";
  evidence: string;
  nextAction: string;
  boundary: string;
}

export interface FundingSourceComparisonRow {
  asset: string;
  okxRate: string;
  coinglassRate: string;
  sourceDelta: string;
  latestPair: string;
  status: string;
  statusTone: "positive" | "negative" | "warning" | "neutral";
  dataNote: string;
  dataTone: "positive" | "negative" | "warning" | "neutral";
  boundary: string;
}

export interface FundingFreshnessAnomalyRow {
  asset: string;
  source: string;
  observations: string;
  latest: string;
  latestRate: string;
  lastChange: string;
  dataStatus: string;
  dataTone: "positive" | "negative" | "warning" | "neutral";
  anomaly: string;
  anomalyTone: "positive" | "negative" | "warning" | "neutral";
  boundary: string;
}

export interface FundingQaDrilldownRow {
  asset: string;
  source: string;
  loadedRows: string;
  rowLatest: string;
  freshness: string;
  freshnessTone: "positive" | "negative" | "warning" | "neutral";
  freshnessReason: string;
  coverage: string;
  coverageTone: "positive" | "negative" | "warning" | "neutral";
  coverageReason: string;
  sync: string;
  syncTone: "positive" | "negative" | "warning" | "neutral";
  nextAction: string;
  boundary: string;
}

export interface FundingAnomalyDetailRow {
  asset: string;
  source: string;
  samples: string;
  latestRate: string;
  baselineAverage: string;
  observedRange: string;
  zScore: string;
  status: string;
  statusTone: "positive" | "negative" | "warning" | "neutral";
  nextReview: string;
  boundary: string;
}

export interface FundingHistoryDiagnosticRow {
  asset: string;
  source: string;
  observations: string;
  window: string;
  latest: string;
  interval: string;
  averageRate: string;
  observedRange: string;
  status: string;
  statusTone: "positive" | "negative" | "warning" | "neutral";
  nextAction: string;
  boundary: string;
}

export interface FundingHistoryControlRow {
  control: string;
  selection: string;
  status: string;
  statusTone: "positive" | "negative" | "warning" | "neutral";
  reason: string;
  nextAction: string;
  boundary: string;
}

export interface FundingHistoryReadinessRow {
  check: string;
  status: string;
  statusTone: "positive" | "negative" | "warning" | "neutral";
  evidence: string;
  nextAction: string;
  boundary: string;
}

export interface FundingMatrixCell {
  asset: string;
  venue: string;
  rate: number;
}

export interface FundingOpportunity {
  asset: string;
  longLeg: string;
  shortLeg: string;
  fundingEdge: number;
  netApr: number;
  liquidityScore: number;
  riskScore: number;
}

export interface LongShortLeg {
  asset: string;
  venue: string;
  receiveSide: "long" | "short";
  currentRate: number;
  estimatedApr: number;
}

export interface AssetDeepDiveData {
  asset: Asset;
  candles: Candle[];
  keyMetrics: Array<{ label: string; value: string; tone?: "positive" | "negative" | "neutral" }>;
  derivatives: Array<{ label: string; value: string; delta?: string; tone?: "positive" | "negative" }>;
  venueBreakdown: SeriesPoint[];
  orderBook: {
    bids: Array<{ price: number; size: number }>;
    asks: Array<{ price: number; size: number }>;
  };
  liquidations: {
    longUsd: number;
    shortUsd: number;
    byVenue: SeriesPoint[];
  };
}

export type MatrixMetric = "price" | "spread" | "openInterest" | "volume" | "liquidity" | "depth" | "slippage";

export interface MarketMatrixData {
  metric: MatrixMetric;
  venues: string[];
  assets: string[];
  rows: MarketMatrixRow[];
  insights: Array<{ label: string; value: string; caption: string; tone?: "positive" | "negative" | "warning" }>;
}

export interface MarketMatrixRow {
  asset: string;
  values: Record<string, number>;
}

export interface StrategyLabData {
  name: string;
  status: "saved" | "draft";
  metrics: KpiMetric[];
  equityCurve: SeriesPoint[];
  drawdown: SeriesPoint[];
  pnlDistribution: SeriesPoint[];
  parameters: Array<{ label: string; value: string }>;
  trades: Array<{
    time: string;
    asset: string;
    side: "Long" | "Short";
    entry: number;
    exit: number;
    pnl: number;
  }>;
}

export interface ArbitrageScannerData {
  opportunities: Array<{
    id: string;
    type: OpportunityType;
    asset: string;
    longLeg: string;
    shortLeg: string;
    edge: number;
    expectedReturn: number;
    liquidity: string;
    fees: number;
    slippage: number;
    riskScore: number;
  }>;
}
