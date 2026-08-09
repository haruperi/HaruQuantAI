import type { Order, OrderSide, Position, Product, SubmitOrderInput, TicketOrderType, TradeLogEntry } from "./market";
import type { WidgetType, Workspace } from "./widget";

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
  oneClickTrading: boolean;
  workspaces: Workspace[];
  activeWorkspaceId: number;
  defaultWorkspaceId: number;
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
  toggleOneClickTrading: () => void;
  resetBalance: () => void;

  // workspaces
  setActiveWorkspace: (id: number) => void;
  setDefaultWorkspace: (id: number) => void;
  renameWorkspace: (id: number, name: string) => void;
  duplicateWorkspace: (id: number) => void;
  deleteWorkspace: (id: number) => void;
  addWorkspace: () => void;

  // widget expand/layout
  expandWidget: (widgetId: string | null) => void;
  contractWidget: () => void;
  toggleExpandWidget: (widgetId: string | null) => void;
  switchExpandedWidget: (widgetId: string) => void;
  reorderWidgets: (sourceWidgetId: string, targetWidgetId: string) => void;
  moveWidgetToCell: (widgetId: string, col: number, row: number) => void;
  resizeWidget: (widgetId: string, colSpan: number, rowSpan: number) => void;
  addWidgetToWorkspace: (widgetType: WidgetType, customTitle?: string, symbol?: string) => void;
  removeWidget: (widgetId: string) => void;

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
