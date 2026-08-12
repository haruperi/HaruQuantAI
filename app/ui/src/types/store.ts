import type { Order, OrderSide, Position, Product, SubmitOrderInput, TicketOrderType, TradeLogEntry } from "./market";

export interface OrderTicketProps {
  symbol: string;
  side: OrderSide;
  type: TicketOrderType;
  defaultTab: "futures" | "options";
  limitPrice?: number | string;
  stopPrice?: number | string;
  cp?: string;
  strike?: string | number;
}

export interface TradingStoreState {
  practiceBalance: number;
  challengeBalance: number;
  netPL: number;
  margin: number;
  available: number;
  ranking: string;
  mode: "practice" | "challenge";
  theme: "dark" | "light";
  products: Product[];
  selectedSymbol: string;
  orders: Order[];
  positions: Position[];
  tradeLog: TradeLogEntry[];
  isOrderTicketOpen: boolean;
  orderTicketProps: OrderTicketProps;
  // System Settings modal open state (in-place popup, no route change).
  isSettingsOpen: boolean;

  // preferences
  setMode: (mode: "practice" | "challenge") => void;
  toggleTheme: () => void;
  resetBalance: () => void;

  // order ticket
  openOrderTicket: (props?: Partial<OrderTicketProps>) => void;
  closeOrderTicket: () => void;

  // system settings modal
  openSettings: () => void;
  closeSettings: () => void;

  // trading engine
  submitOrder: (orderData: SubmitOrderInput) => void;
  flattenPositions: () => void;
  cancelAllOrders: () => void;
  cancelOrder: (orderId: string) => void;

  // realtime simulator
  updateQuotes: () => void;
}
