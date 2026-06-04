import {
  ArbitrageScannerData,
  Asset,
  AssetDeepDiveData,
  Candle,
  FundingData,
  MarketMatrixData,
  MarketOverviewData,
  PerpDexData,
  SeriesPoint,
  StrategyLabData,
} from "@/types/terminal";

const btcSpark = [41, 38, 34, 35, 31, 28, 33, 30, 35, 39, 37, 32, 31, 34, 36];
const ethSpark = [28, 31, 29, 35, 33, 37, 40, 35, 42, 39, 36, 34, 35, 38, 40];
const solSpark = [30, 33, 29, 28, 35, 42, 50, 58, 55, 44, 39, 34, 31, 33, 36];

export const assets: Asset[] = [
  {
    id: "bitcoin",
    symbol: "BTC",
    name: "Bitcoin",
    price: 67452,
    change24h: -1.12,
    change7d: -3.21,
    marketCap: 1_320_000_000_000,
    volume24h: 38_600_000_000,
    volumeToMarketCap: 2.17,
    openInterest: 24_300_000_000,
    perpVolume: 18_900_000_000,
    sparkline: btcSpark,
  },
  {
    id: "ethereum",
    symbol: "ETH",
    name: "Ethereum",
    price: 3120,
    change24h: 0.30,
    change7d: -2.11,
    marketCap: 374_600_000_000,
    volume24h: 15_700_000_000,
    volumeToMarketCap: 4.11,
    openInterest: 9_600_000_000,
    perpVolume: 8_400_000_000,
    sparkline: ethSpark,
  },
  {
    id: "tether",
    symbol: "USDT",
    name: "Tether",
    price: 1,
    change24h: 0.01,
    change7d: 0.02,
    marketCap: 116_000_000_000,
    volume24h: 42_300_000_000,
    volumeToMarketCap: 39.71,
    openInterest: 0,
    perpVolume: 0,
    sparkline: [20, 21, 20, 20, 21, 22, 21, 22, 20, 21, 21, 22, 21, 20, 21],
  },
  {
    id: "binancecoin",
    symbol: "BNB",
    name: "BNB",
    price: 582.21,
    change24h: -0.71,
    change7d: -1.28,
    marketCap: 85_000_000_000,
    volume24h: 1_200_000_000,
    volumeToMarketCap: 1.42,
    openInterest: 1_180_000_000,
    perpVolume: 920_000_000,
    sparkline: [31, 30, 28, 29, 32, 31, 30, 27, 29, 28, 27, 30, 28, 27, 26],
  },
  {
    id: "solana",
    symbol: "SOL",
    name: "Solana",
    price: 152.44,
    change24h: -0.84,
    change7d: -5.21,
    marketCap: 68_000_000_000,
    volume24h: 2_870_000_000,
    volumeToMarketCap: 4.21,
    openInterest: 1_320_000_000,
    perpVolume: 2_670_000_000,
    sparkline: solSpark,
  },
  {
    id: "xrp",
    symbol: "XRP",
    name: "XRP",
    price: 3.12,
    change24h: -1.91,
    change7d: -4.18,
    marketCap: 172_000_000_000,
    volume24h: 2_200_000_000,
    volumeToMarketCap: 1.28,
    openInterest: 940_000_000,
    perpVolume: 1_030_000_000,
    sparkline: [42, 41, 39, 36, 38, 35, 33, 31, 29, 31, 30, 29, 28, 27, 26],
  },
];

const fundingHistory = [
  0.004, -0.006, 0.011, 0.018, -0.004, 0.009, 0.021, -0.012, -0.018, 0.006, 0.014, 0.022,
  -0.006, 0.008, 0.017, 0.026, -0.011, 0.004, 0.015, 0.019,
].map((rate, index) => ({
  time: Date.UTC(2026, 5, 1, index * 4),
  asset: "BTC",
  market: "BTC-USD PERP",
  venue: "Hyperliquid",
  rate,
  annualized: rate * 3 * 365,
}));

export const marketOverviewFixture: MarketOverviewData = {
  kpis: [
    { label: "Total Market Cap", value: "$2.74T", delta: "-1.12%", tone: "negative", sparkline: btcSpark },
    { label: "24h Volume", value: "$87.6B", delta: "+6.18%", tone: "positive", sparkline: ethSpark },
    { label: "BTC Dominance", value: "52.34%", delta: "-0.61%", tone: "negative", sparkline: btcSpark },
    { label: "ETH Dominance", value: "17.28%", delta: "+0.19%", tone: "positive", sparkline: ethSpark },
    { label: "Stablecoin Cap", value: "$158.7B", delta: "+2.32%", tone: "positive", sparkline: [20, 22, 21, 23, 22, 26, 25, 27, 26, 29] },
    { label: "Fear & Greed", value: "63", delta: "Greed", tone: "warning", sparkline: [30, 35, 40, 47, 55, 59, 61, 63] },
  ],
  heatmap: [
    { symbol: "BTC", name: "Bitcoin", value: 42, change24h: -1.12, marketCap: 1_320_000_000_000 },
    { symbol: "ETH", name: "Ethereum", value: 26, change24h: 0.3, marketCap: 374_600_000_000 },
    { symbol: "BNB", name: "BNB", value: 11, change24h: -0.71, marketCap: 85_000_000_000 },
    { symbol: "XRP", name: "XRP", value: 9, change24h: -1.91, marketCap: 172_000_000_000 },
    { symbol: "SOL", name: "Solana", value: 8, change24h: -2.7, marketCap: 68_000_000_000 },
    { symbol: "DOGE", name: "Dogecoin", value: 5, change24h: 0.2, marketCap: 26_000_000_000 },
    { symbol: "ADA", name: "Cardano", value: 5, change24h: -1.1, marketCap: 23_000_000_000 },
    { symbol: "LINK", name: "Chainlink", value: 4, change24h: 1.4, marketCap: 14_000_000_000 },
  ],
  btcOverview: {
    symbol: "BTC",
    name: "Bitcoin",
    price: 67452,
    change24h: -1.12,
    marketCap: 1_320_000_000_000,
    volume24h: 28_600_000_000,
    dominance: 52.34,
    sparkline: btcSpark,
  },
  ethOverview: {
    symbol: "ETH",
    name: "Ethereum",
    price: 3120,
    change24h: 0.3,
    marketCap: 374_600_000_000,
    volume24h: 15_700_000_000,
    dominance: 17.28,
    sparkline: ethSpark,
  },
  marketBreadth: {
    advancing: 61,
    neutral: 14,
    declining: 25,
    histogram: [
      { label: "0", value: 12 },
      { label: "1", value: 18 },
      { label: "2", value: 31 },
      { label: "3", value: 25 },
      { label: "4", value: 17 },
      { label: "5", value: 9 },
    ],
  },
  topGainers: [
    { rank: 1, symbol: "SPX", name: "SPX6900", change24h: 18.41 },
    { rank: 2, symbol: "WIF", name: "dogwifhat", change24h: 12.73 },
    { rank: 3, symbol: "JUP", name: "Jupiter", change24h: 9.31 },
    { rank: 4, symbol: "RNDR", name: "Render", change24h: 8.21 },
    { rank: 5, symbol: "SHIB", name: "Shiba Inu", change24h: 7.06 },
  ],
  topLosers: [
    { rank: 1, symbol: "ARB", name: "Arbitrum", change24h: -9.24 },
    { rank: 2, symbol: "OP", name: "Optimism", change24h: -8.71 },
    { rank: 3, symbol: "IMX", name: "Immutable", change24h: -7.06 },
    { rank: 4, symbol: "MATIC", name: "Polygon", change24h: -6.58 },
    { rank: 5, symbol: "ADA", name: "Cardano", change24h: -5.41 },
  ],
  topAssets: assets,
};

export const perpDexFixture: PerpDexData = {
  kpis: [
    { label: "Total Perp DEX Volume", value: "$42.6B", delta: "+4.14%", tone: "positive", sparkline: [12, 13, 13, 14, 16, 21, 29, 35] },
    { label: "Total Open Interest", value: "$18.7B", delta: "-2.31%", tone: "negative", sparkline: [22, 21, 20, 19, 22, 24, 26, 29] },
    { label: "Active Venues", value: "23", caption: "Tracked protocols", tone: "neutral" },
    { label: "Avg Liquidity Score", value: "78/100", delta: "High", tone: "positive", sparkline: [60, 64, 68, 72, 76, 78] },
  ],
  venues: [
    { id: "hyperliquid", name: "Hyperliquid", type: "perp_dex", share: 35.2, liquidityScore: 92, openInterest: 7_100_000_000, volume24h: 14_900_000_000 },
    { id: "dydx", name: "dYdX", type: "perp_dex", share: 18.7, liquidityScore: 81, openInterest: 3_200_000_000, volume24h: 7_900_000_000 },
    { id: "gmx", name: "GMX", type: "perp_dex", share: 12.4, liquidityScore: 76, openInterest: 2_400_000_000, volume24h: 5_200_000_000 },
    { id: "vertex", name: "Vertex", type: "perp_dex", share: 8.9, liquidityScore: 74, openInterest: 1_800_000_000, volume24h: 3_700_000_000 },
    { id: "drift", name: "Drift", type: "perp_dex", share: 6.4, liquidityScore: 64, openInterest: 1_200_000_000, volume24h: 2_700_000_000 },
  ],
  volumeShare: [
    { label: "Hyperliquid", value: 35.2 },
    { label: "dYdX", value: 18.7 },
    { label: "GMX", value: 12.4 },
    { label: "Vertex", value: 8.9 },
    { label: "Drift", value: 6.4 },
    { label: "Others", value: 18.4 },
  ],
  oiShare: [
    { label: "Hyperliquid", value: 38.1 },
    { label: "dYdX", value: 17.3 },
    { label: "GMX", value: 13.1 },
    { label: "Vertex", value: 9.6 },
    { label: "Drift", value: 6.4 },
    { label: "Others", value: 15.1 },
  ],
  stackedVolume: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"].map((time, index) => ({
    time,
    values: {
      Hyperliquid: 90 + index * 12,
      dYdX: 42 + index * 5,
      GMX: 30 + index * 4,
      Vertex: 24 + index * 3,
      Drift: 18 + index * 2,
    },
  })),
  liquidityMetrics: [
    { venue: "Hyperliquid", score: 92 },
    { venue: "dYdX", score: 81 },
    { venue: "GMX", score: 76 },
    { venue: "Vertex", score: 74 },
    { venue: "Drift", score: 64 },
  ],
  markets: [
    { market: "BTC-PERP", venue: "Hyperliquid", price: 67460, volume24h: 6_400_000_000, openInterest: 3_400_000_000, liquidityScore: 90, oiToVolume: 0.53 },
    { market: "ETH-PERP", venue: "Hyperliquid", price: 3119, volume24h: 3_200_000_000, openInterest: 2_100_000_000, liquidityScore: 90, oiToVolume: 0.66 },
    { market: "SOL-PERP", venue: "Hyperliquid", price: 152.36, volume24h: 2_870_000_000, openInterest: 1_320_000_000, liquidityScore: 83, oiToVolume: 0.46 },
    { market: "BTC-PERP", venue: "dYdX", price: 67440, volume24h: 1_940_000_000, openInterest: 1_290_000_000, liquidityScore: 81, oiToVolume: 0.66 },
    { market: "ETH-PERP", venue: "dYdX", price: 3118, volume24h: 1_120_000_000, openInterest: 900_000_000, liquidityScore: 81, oiToVolume: 0.79 },
  ],
};

export const fundingFixture: FundingData = {
  kpis: [
    { label: "Avg Funding", value: "0.0048%", delta: "+0.011", tone: "positive", sparkline: [10, 11, 12, 15, 13, 16] },
    { label: "Top Positive", value: "0.0321%", caption: "SOL · Hyperliquid", tone: "positive" },
    { label: "Top Negative", value: "-0.0187%", caption: "ETH · dYdX", tone: "negative" },
    { label: "Funding Regime", value: "Positive", caption: "Bullish bias", tone: "warning", sparkline: [20, 21, 23, 26, 27, 29] },
  ],
  venues: ["Binance", "OKX", "Bybit", "Hyperliquid", "dYdX", "Drift"],
  assets: ["BTC", "ETH", "SOL", "BNB", "XRP", "AVAX"],
  matrix: ["BTC", "ETH", "SOL", "BNB", "XRP", "AVAX"].map((asset, row) =>
    ["Binance", "OKX", "Bybit", "Hyperliquid", "dYdX", "Drift"].map((venue, col) => ({
      asset,
      venue,
      rate: [0.010, 0.008, 0.011, 0.006, -0.002, -0.011][col] + row * 0.0015,
    }))
  ),
  history: fundingHistory,
  arbitrage: [
    { asset: "SOL", longLeg: "Spot (Binance)", shortLeg: "Perp (dYdX)", fundingEdge: 0.0423, netApr: 34.8, liquidityScore: 92, riskScore: 18 },
    { asset: "ETH", longLeg: "Spot (Binance)", shortLeg: "Perp (dYdX)", fundingEdge: 0.0364, netApr: 24.2, liquidityScore: 86, riskScore: 24 },
    { asset: "BTC", longLeg: "Spot (Binance)", shortLeg: "Perp (Hyperliquid)", fundingEdge: 0.0311, netApr: 20.4, liquidityScore: 82, riskScore: 28 },
    { asset: "AVAX", longLeg: "Spot (OKX)", shortLeg: "Perp (dYdX)", fundingEdge: 0.0281, netApr: 18.2, liquidityScore: 78, riskScore: 32 },
  ],
  longShortLegs: [
    { asset: "SOL", venue: "dYdX", receiveSide: "short", currentRate: -0.0187, estimatedApr: 34.8 },
    { asset: "AVAX", venue: "dYdX", receiveSide: "short", currentRate: -0.0147, estimatedApr: 24.7 },
    { asset: "MATIC", venue: "dYdX", receiveSide: "short", currentRate: -0.0142, estimatedApr: 21.3 },
  ],
  predicted: ["ETH", "BNB", "SOL", "XRP", "ADA", "AVAX"].map((asset, index) => ({
    time: Date.UTC(2026, 5, 4, index * 4),
    asset,
    market: `${asset}-USD PERP`,
    venue: index % 2 === 0 ? "Binance" : "Hyperliquid",
    rate: [0.0025, 0.0041, 0.0077, 0.0032, 0.0045, 0.0061][index],
    predicted: [0.0027, 0.0038, 0.0081, 0.0034, 0.0042, 0.0064][index],
  })),
};

const solCandles: Candle[] = Array.from({ length: 42 }).map((_, index) => {
  const base = 142 + Math.sin(index / 4) * 8 + index * 0.48;
  return {
    time: Date.UTC(2026, 4, 20 + index),
    open: base - 1.8,
    high: base + 3.2,
    low: base - 3.1,
    close: base + Math.sin(index / 2) * 2,
    volume: 90_000 + index * 4_000,
  };
});

export const assetDeepDiveFixture: AssetDeepDiveData = {
  asset: assets.find((asset) => asset.symbol === "SOL") ?? assets[4],
  candles: solCandles,
  keyMetrics: [
    { label: "24H Change", value: "-0.84%", tone: "negative" },
    { label: "7D Change", value: "-5.21%", tone: "negative" },
    { label: "Market Cap", value: "$68.0B" },
    { label: "24H Volume", value: "$2.87B" },
    { label: "OI / Market Cap", value: "1.94%" },
    { label: "Liquidity Score", value: "82/100", tone: "positive" },
  ],
  derivatives: [
    { label: "Open Interest", value: "$1.32B" },
    { label: "24H Perp Volume", value: "$4.53B" },
    { label: "Liquidations", value: "$8.21M", delta: "+18%", tone: "negative" },
    { label: "Funding Avg", value: "0.0061%", delta: "+", tone: "positive" },
  ],
  venueBreakdown: [
    { label: "Binance", value: 36.1 },
    { label: "OKX", value: 24.7 },
    { label: "Bybit", value: 18.9 },
    { label: "Hyperliquid", value: 10.2 },
    { label: "Others", value: 8.1 },
  ],
  orderBook: {
    bids: [
      { price: 152.40, size: 21_130 },
      { price: 152.47, size: 18_100 },
      { price: 152.46, size: 15_410 },
      { price: 152.05, size: 12_800 },
      { price: 151.94, size: 11_390 },
    ],
    asks: [
      { price: 152.43, size: 21_830 },
      { price: 152.47, size: 24_190 },
      { price: 152.46, size: 23_318 },
      { price: 152.49, size: 20_020 },
      { price: 152.50, size: 19_070 },
    ],
  },
  liquidations: {
    longUsd: 1_200_000,
    shortUsd: 4_000_000,
    byVenue: [
      { label: "Binance", value: 39 },
      { label: "OKX", value: 26 },
      { label: "Bybit", value: 18 },
      { label: "Hyperliquid", value: 11 },
      { label: "Other", value: 6 },
    ],
  },
};

export const marketMatrixFixture: MarketMatrixData = {
  metric: "price",
  venues: ["Binance", "OKX", "Bybit", "Hyperliquid", "dYdX", "Drift"],
  assets: ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "AVAX", "MATIC", "LINK", "ADA"],
  rows: [
    ["BTC", 67452, 67449, 67455, 67460, 67438, 67444],
    ["ETH", 3120, 3119, 3122, 3124, 3118, 3117],
    ["SOL", 152.44, 152.21, 152.31, 152.82, 151.92, 152.06],
    ["BNB", 587.48, 587.46, 586.46, 588.88, 587.98, 587.81],
    ["XRP", 3.126, 3.128, 3.118, 3.128, 3.138, 3.132],
    ["DOGE", 0.198, 0.206, 0.208, 0.286, 0.288, 0.285],
    ["AVAX", 37.986, 37.506, 37.965, 37.885, 37.985, 37.981],
    ["MATIC", 0.388, 0.335, 0.275, 0.398, 0.335, 0.336],
    ["LINK", 19.906, 19.506, 19.596, 19.038, 19.098, 19.095],
    ["ADA", 1.988, 1.308, 1.918, 1.895, 1.886, 1.89],
  ].map(([asset, ...values]) => ({
    asset: String(asset),
    values: Object.fromEntries(["Binance", "OKX", "Bybit", "Hyperliquid", "dYdX", "Drift"].map((venue, index) => [venue, Number(values[index])])),
  })),
  insights: [
    { label: "Best Price", value: "SOL Hyperliquid", caption: "$152.82", tone: "positive" },
    { label: "Worst Price", value: "SOL dYdX", caption: "$151.92", tone: "negative" },
    { label: "Max Spread", value: "BTC", caption: "0.22%", tone: "warning" },
    { label: "Low Liquidity", value: "MATIC", caption: "dYdX", tone: "negative" },
    { label: "Stale Data", value: "ADA", caption: "Drift", tone: "warning" },
  ],
};

const lineSeries = (length: number, start: number, drift: number): SeriesPoint[] =>
  Array.from({ length }).map((_, index) => ({
    label: `${index + 1}`,
    value: start + index * drift + Math.sin(index / 3) * 4,
  }));

export const strategyLabFixture: StrategyLabData = {
  name: "Mean Reversion After High Funding",
  status: "saved",
  metrics: [
    { label: "Net PnL", value: "-$11,550.00", delta: "-14.0%", tone: "negative" },
    { label: "Sharpe Ratio", value: "-1.18", tone: "negative" },
    { label: "Max Drawdown", value: "-22.43%", tone: "negative" },
    { label: "Win Rate", value: "36.2%", tone: "neutral" },
    { label: "Total Trades", value: "70", tone: "neutral" },
    { label: "Profit Factor", value: "0.72", tone: "negative" },
  ],
  equityCurve: lineSeries(36, 0, -1.1),
  drawdown: lineSeries(36, -2, -0.72),
  pnlDistribution: [
    { label: "-15", value: 2 },
    { label: "-10", value: 6 },
    { label: "-5", value: 14 },
    { label: "0", value: 38 },
    { label: "5", value: 28 },
    { label: "10", value: 12 },
    { label: "15", value: 4 },
  ],
  parameters: [
    { label: "Entry Funding", value: "0.12%" },
    { label: "Exit Funding", value: "0.002%" },
    { label: "Holding Period", value: "8h" },
    { label: "Stop Loss", value: "0.75%" },
    { label: "Leverage", value: "1.0x" },
    { label: "Fees", value: "0.06%" },
    { label: "Slippage", value: "0.15%" },
  ],
  trades: [
    { time: "Jun 9 12:00", asset: "SOL", side: "Short", entry: 152.8, exit: 151.4, pnl: 0.92 },
    { time: "Jun 9 04:00", asset: "ETH", side: "Short", entry: 3128.21, exit: 3105.6, pnl: 0.73 },
    { time: "Jun 8 20:00", asset: "BTC", side: "Short", entry: 67990, exit: 67200, pnl: 0.44 },
    { time: "Jun 8 12:00", asset: "SOL", side: "Long", entry: 153.21, exit: 151.8, pnl: -0.91 },
    { time: "Jun 8 04:00", asset: "ETH", side: "Long", entry: 3130.13, exit: 3150.2, pnl: -1.41 },
    { time: "Jun 7 20:00", asset: "BTC", side: "Long", entry: 67980, exit: 60720, pnl: -1.07 },
  ],
};

export const arbitrageScannerFixture: ArbitrageScannerData = {
  opportunities: [
    { id: "basis-sol-1", type: "basis", asset: "SOL", longLeg: "Spot Binance", shortLeg: "Perp Hyperliquid", edge: 0.42, expectedReturn: 18.4, liquidity: "High", fees: 0.06, slippage: 0.11, riskScore: 22 },
    { id: "spread-btc-1", type: "cross_exchange", asset: "BTC", longLeg: "OKX Spot", shortLeg: "Bybit Spot", edge: 0.18, expectedReturn: 7.2, liquidity: "High", fees: 0.08, slippage: 0.04, riskScore: 16 },
    { id: "oi-eth-1", type: "oi_divergence", asset: "ETH", longLeg: "Spot Binance", shortLeg: "Perp dYdX", edge: 0.31, expectedReturn: 12.8, liquidity: "Medium", fees: 0.07, slippage: 0.18, riskScore: 35 },
    { id: "liq-matic-1", type: "liquidity", asset: "MATIC", longLeg: "Spot OKX", shortLeg: "Perp Drift", edge: 0.24, expectedReturn: 9.6, liquidity: "Thin", fees: 0.09, slippage: 0.22, riskScore: 48 },
  ],
};
