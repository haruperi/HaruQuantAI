/** Owner-local presentation/resource documents; no backend execution authority. */
export interface MTStatementTrade {
  ticket: number;
  openTime: string;
  type: 'buy' | 'sell';
  size: number;
  item: string;
  openPrice: number;
  closeTime: string;
  closePrice: number;
  commission: number;
  swap: number;
  profit: number;
  pips: number;
  comment?: string;
  magicNumber?: number;
}

export interface MTAnalysisMetrics {
  initialDeposit: number;
  totalNetProfit: number;
  grossProfit: number;
  grossLoss: number;
  profitFactor: number;
  expectedPayoff: number;
  absoluteDrawdown: number;
  maximalDrawdown: number;
  maximalDrawdownPercent: number;
  totalTrades: number;
  winRate: number;
  profitTrades: number;
  lossTrades: number;
  averageProfit: number;
  averageLoss: number;
  profitRatio: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;
  sharpeRatio: number;
  sqn: number;
}

export interface MTFilterOptions {
  symbol: string;
  magicNumber: string;
  comment: string;
  excludeBalanceOrders: boolean;
}
