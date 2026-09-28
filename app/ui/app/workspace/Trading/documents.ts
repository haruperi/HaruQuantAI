/** Owner-local presentation/resource documents; no backend execution authority. */
export type OrderKind = 'Market' | 'Limit' | 'Stop';

export type OrderSide = 'Buy' | 'Sell';

export interface BrokerAccount {
  id: string;
  broker: string;
  accountNumber: string;
  server: string;
  connected: boolean;
  latencyMs: number;
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  marginLevel: number;
  currency: string;
  leverage: number;
}

export interface ExecutionLogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS';
  source: string;
  message: string;
}

export interface PendingOrder {
  id: string;
  ticket: number;
  symbol: string;
  kind: 'Buy Limit' | 'Sell Limit' | 'Buy Stop' | 'Sell Stop';
  lots: number;
  orderPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  expiration: string;
  magicNumber: number;
  comment: string;
}

export interface Position {
  id: string;
  ticket: number;
  symbol: string;
  side: OrderSide;
  lots: number;
  openPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  swap: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  magicNumber: number;
  comment: string;
}
