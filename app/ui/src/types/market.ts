export interface Product {
  symbol: string;
  adr10: number;
  atr14: number;
  decimals: number;
  name: string;
  assetClass: string;
  contractMonth: string;
  lastPrice: number;
  change: number;
  changePercent: number;
  open: number;
  priorSettle: number;
  high: number;
  low: number;
  volume: number;
  bid: number;
  ask: number;
}

export type OrderSide = "BUY" | "SELL";
export type OrderTypeCode = "MKT" | "LMT" | "STP";
export type OrderStatus = "Working" | "Filled" | "Cancelled";

export interface Order {
  id: string;
  side: OrderSide;
  symbol: string;
  month: string;
  strike: string | number;
  cp: string;
  qty: number;
  leaves: number;
  type: OrderTypeCode;
  fillPx: number | string;
  limitPx: number | string;
  stopPx: number | string;
  status: OrderStatus;
  timestamp: string;
}

export interface Position {
  symbol: string;
  contract: string;
  month: string;
  strike: string | number;
  cp: string;
  position: string;
  buys: number;
  sells: number;
  averagePx: number;
  unrealizedPL: number;
  realizedPL: number;
}

export type OpenClose = "Open" | "Close";
export type TicketOrderType = "Market" | "Limit" | "Stop";

export interface TradeLogEntry {
  id: number;
  symbol: string;
  transactionDate: string;
  openClose: OpenClose;
  side: OrderSide;
  cp: string;
  strike: string | number;
  qty: number;
  type: OrderTypeCode;
  px: number;
  tif: string;
  fillPx: number;
  stop: string;
  stopPx: string;
  notes: string;
}

export interface OptionsSide {
  low: number;
  high: number;
  prior: number;
  change: number;
  last: number;
  qty: number;
  bid: number;
  offer: number;
}

export interface OptionsGridRow {
  strike: number;
  isATM: boolean;
  calls: OptionsSide;
  puts: OptionsSide;
}

export interface SubmitOrderInput {
  symbol: string;
  side: OrderSide;
  qty: number;
  orderType: TicketOrderType;
  limitPrice?: number;
  stopPrice?: number;
  tif?: string;
  cp?: string;
  strike?: string | number;
}
