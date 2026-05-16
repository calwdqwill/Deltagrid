export interface ScannerPreferences {
  language: string;
  minSpreadPct: number;
  minVolume24h?: number;
  refreshIntervalSec: number;
  slippagePct: number;
  feeBuyPct: number;
  feeSellPct: number;
  positiveNetOnly: boolean;
  selectedTypes: string[];
}

export interface FavoritesResponse {
  instrumentIds: string[];
}

export interface PinnedResponse {
  instrumentIds: string[];
}
