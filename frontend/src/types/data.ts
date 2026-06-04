export interface OHLCVCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface FundingRate {
  timestamp: number;
  symbol: string;
  exchange: string;
  rate: number;
  intervalHours: number;
}

export interface OpenInterest {
  timestamp: number;
  symbol: string;
  exchange: string;
  oiValue: number;
}

export interface Liquidation {
  timestamp: number;
  symbol: string;
  exchange: string;
  side: "long" | "short";
  qty: number;
  usd: number;
}

export interface LongShortRatio {
  timestamp: number;
  symbol: string;
  exchange: string;
  longRatio: number;
  shortRatio: number;
}

export interface Instrument {
  id: string;
  symbol: string;
  exchange: string;
  base: string;
  quote: string;
  aliases: Record<string, string>;
}

export interface DataQualityScore {
  completeness: number;
  freshness: number;
  consistency: number;
  overall: number;
}
