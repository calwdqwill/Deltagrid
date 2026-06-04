export interface BacktestConfig {
  id: string;
  strategyType: "funding_mean_reversion" | "basis_compression" | "liquidation_cascade";
  symbols: string[];
  exchanges: string[];
  timeframe: number;
  params: Record<string, number>;
}

export interface BacktestResult {
  id: string;
  configId: string;
  totalReturn: number;
  sharpe: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  feesDrag: number;
  fundingContribution: number;
  tradesCount: number;
}

export interface BacktestTrade {
  timestamp: number;
  symbol: string;
  side: "long" | "short";
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  fees: number;
  fundingPnl: number;
}

export interface BacktestEquityPoint {
  timestamp: number;
  equity: number;
  drawdown: number;
}
