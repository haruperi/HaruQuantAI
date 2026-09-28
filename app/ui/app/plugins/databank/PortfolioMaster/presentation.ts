/** Owner-local presentation/resource documents; no backend execution authority. */
export interface Strategy {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  direction: 'Both' | 'Long' | 'Short';
  bankId: string;
  revision: number;
  note: string;
  metrics: {
    netProfit: number;
    trades: number;
    profitFactor: number;
    maxDrawdown: number;
    sharpe: number;
    stability: number;
  };
  trades: Trade[];
  equity: EquityPoint[];
  parameters: Record<string, number>;
}

export interface Databank {
  id: string;
  name: string;
  strategyIds: string[];
}

export interface Trade {
  id: string;
  strategyId: string;
  side: 'Long' | 'Short';
  entryTime: string;
  exitTime: string;
  entry: number;
  exit: number;
  size: number;
  pnl: number;
  sample: 'IS' | 'OOS';
}

export interface EquityPoint {
  time: string;
  value: number;
  drawdown: number;
}
