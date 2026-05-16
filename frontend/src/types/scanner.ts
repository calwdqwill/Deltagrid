export type ScannerType = "cex-cex" | "dex-cex" | "spot-perp";

export type DataStatus = "live" | "cached" | "stale" | "fallback" | "partial" | "unavailable";

export type SignalLevel = "STRONG" | "BUY_SELL" | "MARGINAL" | "HOLD";

export interface ScannerRecord {
  id: string;
  tokenName: string;
  symbol: string;
  pair: string;
  iconUrl?: string;
  scannerType: ScannerType;
  buyVenue: string;
  buyPrice: number;
  sellVenue: string;
  sellPrice: number;
  spreadPct: number;
  netProfitPct: number;
  volume24h?: number;
  signal: SignalLevel;
  trendSeries: number[];
  dataStatus: DataStatus;
  sourceLabel: string;
  updatedAt: string;
  isFavorite: boolean;
  isPinned: boolean;
  basisPct?: number;
  fundingRate?: number;
  openInterest?: number;
  strategyHint?: string;
}

export interface ScannerMeta {
  total: number;
  filtered: number;
  dataStatusCounts: Record<string, number>;
  lastUpdated?: string;
  sources: string[];
  isFallback: boolean;
}

export interface ScannerListResponse {
  records: ScannerRecord[];
  meta: ScannerMeta;
}

export interface ScannerFilters {
  type: string;
  minSpread: number;
  minVolume?: number;
  search: string;
  positiveNetOnly: boolean;
}
