import { fetchServerApi } from "@/lib/server-api";
import {
  Asset,
  AssetDeepDiveData,
  AssetSnapshot,
  Candle,
  KpiMetric,
  MarketHeatmapItem,
  MarketOverviewData,
  RankedAssetMove,
  SeriesPoint,
} from "@/types/terminal";
import { DataHealthPayload } from "./live-data";

interface MarketCoin {
  id: string;
  name: string;
  symbol: string;
  image?: string | null;
  current_price?: number | null;
  market_cap?: number | null;
  market_cap_rank?: number | null;
  price_change_percentage_24h?: number | null;
  price_change_percentage_7d?: number | null;
  total_volume?: number | null;
}

interface GlobalMarketPayload {
  total_market_cap_usd?: number;
  total_volume_24h_usd?: number;
  btc_dominance?: number;
  eth_dominance?: number;
  active_cryptocurrencies?: number;
  updated_at?: string;
}

interface FearGreedPoint {
  value: number;
  classification: string;
  timestamp: number;
  time_until_update?: number;
}

interface MarketFundingRate {
  symbol: string;
  rate: number;
  interval: string;
  exchange: string;
  annualized?: number;
  open_interest_usd?: number | null;
  price?: number | null;
  data_status?: string;
}

const STABLE_SYMBOLS = new Set([
  "USDT",
  "USDC",
  "USDE",
  "USDS",
  "USDH",
  "DAI",
  "FDUSD",
  "TUSD",
  "USDD",
  "PYUSD",
  "USDP",
  "GUSD",
  "LUSD",
  "FRAX",
  "SUSD",
  "USD1",
]);

const STABLE_IDS = new Set([
  "tether",
  "usd-coin",
  "ethena-usde",
  "usds",
  "usdh",
  "dai",
  "first-digital-usd",
  "true-usd",
  "usdd",
  "paypal-usd",
  "paxos-standard",
  "gemini-dollar",
  "liquity-usd",
  "frax",
  "nusd",
  "susd",
  "usual-usd",
  "usde",
  "usd1",
]);

interface OhlcvRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  interval: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
  quote_volume?: number | null;
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

const DEFAULT_PERP_EXCHANGE = "okx";
const DEFAULT_PERP_EXCHANGE_LABEL = "OKX";

export interface LiveMarketOverview {
  data: MarketOverviewData;
  fearGreed: FearGreedPoint[];
  statusLabel: string;
  statusTone: "positive" | "warning";
}

export interface LiveAssetDeepDive {
  data: AssetDeepDiveData;
  statusLabel: string;
  statusTone: "positive" | "warning";
  sourceRows: Array<[string, string]>;
}

function toNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function formatCompactCurrency(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (abs >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

function formatSignedPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(Math.abs(value) < 1 ? 3 : 2)}%`;
}

function simpleSparkline(currentValue: number, changePercent: number, points = 12): number[] {
  if (!currentValue) return Array.from({ length: points }, () => 0);

  const startValue = currentValue / (1 + changePercent / 100 || 1);
  return Array.from({ length: points }, (_, index) => {
    const progress = index / Math.max(points - 1, 1);
    return startValue + (currentValue - startValue) * progress;
  });
}

function ohlcvSparkline(rows: OhlcvRow[], fallback: number[]): number[] {
  const prices = rows
    .slice(-96)
    .map((row) => toNumber(row.close))
    .filter((value) => value > 0);

  return prices.length > 1 ? prices : fallback;
}

function recentOhlcvPath(symbol: string, lookbackHours = 8): string {
  const start = Date.now() - lookbackHours * 60 * 60 * 1000;
  return `/data/ohlcv?symbol=${symbol}&exchange=${DEFAULT_PERP_EXCHANGE}&interval=1m&start=${start}`;
}

type KpiTone = NonNullable<KpiMetric["tone"]>;
type AssetMetricTone = NonNullable<AssetDeepDiveData["keyMetrics"][number]["tone"]>;
type DerivativeTone = NonNullable<AssetDeepDiveData["derivatives"][number]["tone"]>;

function marketTone(value: number): KpiTone {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function assetMetricTone(value: number): AssetMetricTone {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function derivativeTone(value: number): DerivativeTone | undefined {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return undefined;
}

function coinSymbol(coin: MarketCoin): string {
  return (coin.symbol || coin.id || "").toUpperCase();
}

function isStableLikeCoin(coin: MarketCoin): boolean {
  const symbol = coinSymbol(coin);
  const id = coin.id.toLowerCase();
  const name = coin.name.toLowerCase();

  if (STABLE_SYMBOLS.has(symbol) || STABLE_IDS.has(id)) return true;
  if (symbol.includes("USD") && symbol !== "XRP") return true;
  if (name.includes("stablecoin") || name.includes("usd coin") || name.includes("dollar")) return true;
  if (name.includes("tether") || name.includes("usde")) return true;

  return false;
}

function mapCoinToAsset(
  coin: MarketCoin,
  fundingBySymbol: Map<string, MarketFundingRate>,
  historyBySymbol: Map<string, number[]> = new Map()
): Asset {
  const symbol = coinSymbol(coin);
  const price = toNumber(coin.current_price);
  const marketCap = toNumber(coin.market_cap);
  const volume24h = toNumber(coin.total_volume);
  const change24h = toNumber(coin.price_change_percentage_24h);
  const change7d = toNumber(coin.price_change_percentage_7d);
  const funding = fundingBySymbol.get(symbol);

  return {
    id: coin.id,
    symbol,
    name: coin.name,
    image: coin.image,
    price,
    change24h,
    change7d,
    marketCap,
    volume24h,
    volumeToMarketCap: marketCap > 0 ? (volume24h / marketCap) * 100 : 0,
    openInterest: toNumber(funding?.open_interest_usd),
    perpVolume: 0,
    sparkline: historyBySymbol.get(symbol) ?? simpleSparkline(price, change24h),
  };
}

function mapCoinToSnapshot(
  coin: MarketCoin | undefined,
  dominance?: number,
  historyBySymbol: Map<string, number[]> = new Map()
): AssetSnapshot {
  if (!coin) {
    return {
      symbol: "-",
      name: "No data",
      image: null,
      price: 0,
      change24h: 0,
      marketCap: 0,
      volume24h: 0,
      dominance,
      sparkline: [0, 0],
    };
  }

  const price = toNumber(coin.current_price);
  const change24h = toNumber(coin.price_change_percentage_24h);

  return {
    symbol: coinSymbol(coin),
    name: coin.name,
    image: coin.image,
    price,
    change24h,
    marketCap: toNumber(coin.market_cap),
    volume24h: toNumber(coin.total_volume),
    dominance,
    sparkline: historyBySymbol.get(coinSymbol(coin)) ?? simpleSparkline(price, change24h),
  };
}

function mapRankedMoves(coins: MarketCoin[], positive: boolean): RankedAssetMove[] {
  return coins
    .filter((coin) => (toNumber(coin.price_change_percentage_24h) > 0) === positive)
    .sort((a, b) => {
      const left = toNumber(a.price_change_percentage_24h);
      const right = toNumber(b.price_change_percentage_24h);
      return positive ? right - left : left - right;
    })
    .slice(0, 5)
    .map((coin, index) => ({
      rank: index + 1,
      symbol: coinSymbol(coin),
      name: coin.name,
      change24h: toNumber(coin.price_change_percentage_24h),
    }));
}

function marketBreadth(coins: MarketCoin[]): MarketOverviewData["marketBreadth"] {
  const total = coins.length || 1;
  const advancingCount = coins.filter((coin) => toNumber(coin.price_change_percentage_24h) > 0.1).length;
  const decliningCount = coins.filter((coin) => toNumber(coin.price_change_percentage_24h) < -0.1).length;
  const neutralCount = Math.max(0, coins.length - advancingCount - decliningCount);
  const buckets = [-20, -10, -5, 0, 5, 10, 20];
  const histogram: SeriesPoint[] = buckets.map((bucket, index) => {
    const next = buckets[index + 1] ?? Number.POSITIVE_INFINITY;
    return {
      label: `${bucket}`,
      value: coins.filter((coin) => {
        const change = toNumber(coin.price_change_percentage_24h);
        return change >= bucket && change < next;
      }).length,
    };
  });

  return {
    advancing: Math.round((advancingCount / total) * 100),
    neutral: Math.round((neutralCount / total) * 100),
    declining: Math.round((decliningCount / total) * 100),
    histogram,
  };
}

function heatmapItems(coins: MarketCoin[]): MarketHeatmapItem[] {
  return coins.slice(0, 12).map((coin) => ({
    symbol: coinSymbol(coin),
    name: coin.name,
    image: coin.image,
    price: toNumber(coin.current_price),
    value: toNumber(coin.market_cap),
    change24h: toNumber(coin.price_change_percentage_24h),
    marketCap: toNumber(coin.market_cap),
  }));
}

function buildKpis(
  global: GlobalMarketPayload | null,
  markets: MarketCoin[],
  fearGreed: FearGreedPoint[],
  fundingRates: MarketFundingRate[],
  health: DataHealthPayload | null
): KpiMetric[] {
  const latestFearGreed = fearGreed[0];
  const liveFunding = fundingRates.filter((item) => item.data_status === "live");
  const avgFunding = liveFunding.length
    ? liveFunding.reduce((sum, item) => sum + toNumber(item.rate), 0) / liveFunding.length
    : 0;

  return [
    {
      label: "Total Market Cap",
      value: formatCompactCurrency(toNumber(global?.total_market_cap_usd)),
      caption: "CoinGecko global",
      tone: "neutral",
    },
    {
      label: "24h Volume",
      value: formatCompactCurrency(toNumber(global?.total_volume_24h_usd)),
      caption: `${markets.length} top assets loaded`,
      tone: "neutral",
    },
    {
      label: "BTC Dominance",
      value: `${toNumber(global?.btc_dominance).toFixed(2)}%`,
      caption: "Global market share",
      tone: "neutral",
    },
    {
      label: "ETH Dominance",
      value: `${toNumber(global?.eth_dominance).toFixed(2)}%`,
      caption: "Global market share",
      tone: "neutral",
    },
    {
      label: "Fear & Greed",
      value: latestFearGreed ? String(latestFearGreed.value) : "No data",
      caption: latestFearGreed?.classification,
      tone: latestFearGreed && latestFearGreed.value <= 40 ? "negative" : "warning",
    },
    {
      label: "Avg Funding",
      value: liveFunding.length ? formatSignedPercent(avgFunding) : "No data",
      caption: health ? `${health.row_counts.funding_rates ?? 0} DB rows` : "Data health unavailable",
      tone: marketTone(avgFunding),
    },
  ];
}

function emptyMarketData(): MarketOverviewData {
  return {
    kpis: [
      {
        label: "Market Data",
        value: "No data",
        caption: "Backend returned empty market payload",
        tone: "warning",
      },
    ],
    heatmap: [],
    btcOverview: mapCoinToSnapshot(undefined),
    ethOverview: mapCoinToSnapshot(undefined),
    marketBreadth: { advancing: 0, neutral: 0, declining: 0, histogram: [] },
    topGainers: [],
    topLosers: [],
    topAssets: [],
  };
}

export async function getLiveMarketOverview(): Promise<LiveMarketOverview> {
  const [
    marketsResponse,
    globalResponse,
    fearGreedResponse,
    fundingResponse,
    healthResponse,
    btcOhlcvResponse,
    ethOhlcvResponse,
    solOhlcvResponse,
  ] = await Promise.all([
    fetchServerApi<MarketCoin[]>("/market/markets?limit=80"),
    fetchServerApi<GlobalMarketPayload>("/market/global"),
    fetchServerApi<FearGreedPoint[]>("/market/fear-greed"),
    fetchServerApi<MarketFundingRate[]>("/market/funding-rates"),
    fetchServerApi<DataHealthPayload>("/data/health"),
    fetchServerApi<OhlcvRow[]>(recentOhlcvPath("BTC")),
    fetchServerApi<OhlcvRow[]>(recentOhlcvPath("ETH")),
    fetchServerApi<OhlcvRow[]>(recentOhlcvPath("SOL")),
  ]);

  const rawMarkets = marketsResponse?.success ? marketsResponse.data : [];
  const markets = rawMarkets.filter((coin) => !isStableLikeCoin(coin)).slice(0, 30);
  const global = globalResponse?.success ? globalResponse.data : null;
  const fearGreed = fearGreedResponse?.success ? fearGreedResponse.data : [];
  const fundingRates = fundingResponse?.success ? fundingResponse.data : [];
  const health = healthResponse?.success ? healthResponse.data : null;
  const fundingBySymbol = new Map(fundingRates.map((item) => [item.symbol.toUpperCase(), item]));
  const historyBySymbol = new Map<string, number[]>();

  if (btcOhlcvResponse?.success) {
    historyBySymbol.set("BTC", ohlcvSparkline(btcOhlcvResponse.data, []));
  }
  if (ethOhlcvResponse?.success) {
    historyBySymbol.set("ETH", ohlcvSparkline(ethOhlcvResponse.data, []));
  }
  if (solOhlcvResponse?.success) {
    historyBySymbol.set("SOL", ohlcvSparkline(solOhlcvResponse.data, []));
  }

  if (!markets.length) {
    return {
      data: emptyMarketData(),
      fearGreed,
      statusLabel: "Market API empty",
      statusTone: "warning",
    };
  }

  const btc = markets.find((coin) => coin.id === "bitcoin" || coinSymbol(coin) === "BTC");
  const eth = markets.find((coin) => coin.id === "ethereum" || coinSymbol(coin) === "ETH");

  return {
    data: {
      kpis: buildKpis(global, markets, fearGreed, fundingRates, health),
      heatmap: heatmapItems(markets),
      btcOverview: mapCoinToSnapshot(btc, global?.btc_dominance, historyBySymbol),
      ethOverview: mapCoinToSnapshot(eth, global?.eth_dominance, historyBySymbol),
      marketBreadth: marketBreadth(markets),
      topGainers: mapRankedMoves(markets, true),
      topLosers: mapRankedMoves(markets, false),
      topAssets: markets.map((coin) => mapCoinToAsset(coin, fundingBySymbol, historyBySymbol)),
    },
    fearGreed,
    statusLabel: "Live market API",
    statusTone: "positive",
  };
}

function mapOhlcv(rows: OhlcvRow[]): Candle[] {
  return rows.slice(-240).map((row) => ({
    time: row.timestamp,
    open: row.open,
    high: row.high,
    low: row.low,
    close: row.close,
    volume: row.quote_volume ?? row.volume ?? undefined,
  }));
}

function mapLiquidations(rows: LiquidationRow[]): AssetDeepDiveData["liquidations"] {
  const totals = rows.reduce(
    (acc, row) => {
      const value = toNumber(row.value_usd);
      const side = row.side.toLowerCase();
      if (side.includes("long") || side === "buy") {
        acc.longUsd += value;
      } else if (side.includes("short") || side === "sell") {
        acc.shortUsd += value;
      }
      acc.byVenue.set(row.exchange, (acc.byVenue.get(row.exchange) ?? 0) + value);
      return acc;
    },
    { longUsd: 0, shortUsd: 0, byVenue: new Map<string, number>() }
  );
  const totalByVenue = Array.from(totals.byVenue.values()).reduce((sum, value) => sum + value, 0);

  return {
    longUsd: totals.longUsd,
    shortUsd: totals.shortUsd,
    byVenue: totalByVenue
      ? Array.from(totals.byVenue.entries()).map(([label, value]) => ({
          label,
          value: (value / totalByVenue) * 100,
        }))
      : [],
  };
}

export async function getLiveAssetDeepDive(symbol: string): Promise<LiveAssetDeepDive> {
  const normalizedSymbol = symbol.toUpperCase();
  const [marketsResponse, fundingResponse, ohlcvResponse, liquidationsResponse, healthResponse] = await Promise.all([
    fetchServerApi<MarketCoin[]>("/market/markets?limit=50"),
    fetchServerApi<MarketFundingRate[]>("/market/funding-rates"),
    fetchServerApi<OhlcvRow[]>(recentOhlcvPath(normalizedSymbol)),
    fetchServerApi<LiquidationRow[]>(`/data/liquidations?symbol=${normalizedSymbol}&exchange=${DEFAULT_PERP_EXCHANGE}`),
    fetchServerApi<DataHealthPayload>("/data/health"),
  ]);

  const markets = marketsResponse?.success ? marketsResponse.data : [];
  const fundingRates = fundingResponse?.success ? fundingResponse.data : [];
  const health = healthResponse?.success ? healthResponse.data : null;
  const fundingBySymbol = new Map(fundingRates.map((item) => [item.symbol.toUpperCase(), item]));
  const market = markets.find((coin) => coinSymbol(coin) === normalizedSymbol);
  const fallbackFunding = fundingBySymbol.get(normalizedSymbol);
  const coin = market ?? {
    id: normalizedSymbol.toLowerCase(),
    name: normalizedSymbol,
    symbol: normalizedSymbol,
    current_price: fallbackFunding?.price ?? 0,
    market_cap: 0,
    total_volume: 0,
    price_change_percentage_24h: 0,
    price_change_percentage_7d: 0,
  };
  const asset = mapCoinToAsset(coin, fundingBySymbol);
  const funding = fundingBySymbol.get(normalizedSymbol);
  const candles = ohlcvResponse?.success ? mapOhlcv(ohlcvResponse.data) : [];
  const liquidations = liquidationsResponse?.success ? mapLiquidations(liquidationsResponse.data) : { longUsd: 0, shortUsd: 0, byVenue: [] };

  const data: AssetDeepDiveData = {
    asset,
    candles,
    keyMetrics: [
      { label: "24H Change", value: formatSignedPercent(asset.change24h), tone: assetMetricTone(asset.change24h) },
      { label: "7D Change", value: formatSignedPercent(asset.change7d), tone: assetMetricTone(asset.change7d) },
      { label: "Market Cap", value: formatCompactCurrency(asset.marketCap) },
      { label: "24H Volume", value: formatCompactCurrency(asset.volume24h) },
      { label: "Open Interest", value: formatCompactCurrency(asset.openInterest) },
      { label: "Data Rows", value: String(health?.row_counts.ohlcv ?? 0) },
    ],
    derivatives: [
      { label: "Funding", value: funding ? formatSignedPercent(toNumber(funding.rate)) : "No data", tone: derivativeTone(toNumber(funding?.rate)) },
      { label: "Annualized Funding", value: funding?.annualized !== undefined ? `${funding.annualized.toFixed(2)}%` : "No data" },
      { label: "Open Interest", value: formatCompactCurrency(toNumber(funding?.open_interest_usd)) },
      { label: "Funding Source", value: funding?.exchange ?? "No data" },
    ],
    venueBreakdown: [],
    orderBook: { bids: [], asks: [] },
    liquidations,
  };

  return {
    data,
    statusLabel: market || fallbackFunding ? "Live market API" : "Asset data empty",
    statusTone: market || fallbackFunding ? "positive" : "warning",
    sourceRows: [
      ["Spot market", market ? "CoinGecko /markets" : "No data"],
      ["Funding/OI", funding ? `${funding.exchange} live` : "No data"],
      ["OHLCV", candles.length ? `${candles.length} ${DEFAULT_PERP_EXCHANGE_LABEL} candles` : "No data"],
      ["Liquidations", liquidations.byVenue.length ? `${DEFAULT_PERP_EXCHANGE_LABEL} live` : "No rows"],
    ],
  };
}
