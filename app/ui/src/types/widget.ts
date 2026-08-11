export type WidgetType =
  | "markets"
  | "watchlist"
  | "chart"
  | "priceLadder"
  | "optionsGrid"
  | "positions"
  | "tradeLog"
  | "tradePlan"
  | "education"
  | "challenges"
  | "dashboard"
  | "data"
  | "strategies"
  | "research"
  | "optimization"
  | "portfolio"
  | "agentic"
  | "simulation"
  | "risk"
  | "trading"
  | "indicators";

export interface Widget {
  id: string;
  type: WidgetType;
  title: string;
  symbol?: string;
  col?: number;
  row?: number;
  colSpan: number;
  rowSpan: number;
}

export interface Workspace {
  id: number;
  name: string;
  expandedWidgetId: string | null;
  widgets: Widget[];
}

export interface GridRect {
  col: number;
  row: number;
  colSpan: number;
  rowSpan: number;
}
