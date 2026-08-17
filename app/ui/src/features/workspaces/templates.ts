/**
 * Workspace template catalog (FEAT-UI-01, FR-UI-195 through FR-UI-197).
 *
 * Templates seed a newly created workspace with a curated widget set,
 * mirroring the CME Group Simulator's "NEW WORKSPACE" template picker.
 * Presets use registered widget types only (FR-UI-023) and explicit grid
 * rectangles so each template opens as a readable layout rather than a
 * stacked column. Symbol-bound presets are EURUSD-bound by owner decision.
 *
 * Every preset's rectangle set reproduces the exact panel orientation of
 * its reference thumbnail in `app/ui/public/templates/` (owner-supplied
 * CME-style renders, Dark/Light variants), measured from the thumbnails'
 * panel-gap pixels. Column and row counts are per-template nominal grids:
 * only the ratios between spans drive the produced docking layout, so a
 * template may use a finer grid than another to express its proportions
 * (e.g. five equal ladders need a 20-column grid).
 */
import type { WidgetType } from "./contracts";

/** Everything a template needs to stamp out one widget in a new workspace. */
export interface WidgetPreset {
  type: WidgetType;
  title: string;
  symbol?: string;
  col: number;
  row: number;
  colSpan: number;
  rowSpan: number;
}

/** One selectable workspace template. */
export interface WorkspaceTemplate {
  id: WorkspaceTemplateId;
  /** Card label shown in the picker. */
  name: string;
  /** Workspace name applied with the template; undefined keeps the deterministic name (Blank). */
  workspaceName?: string;
  widgets: WidgetPreset[];
}

export type WorkspaceTemplateId = "blank" | "haruquant" | "chart-ladder" | "multicharts-ladder" | "options" | "charts";

export const WORKSPACE_TEMPLATES: readonly WorkspaceTemplate[] = [
  {
    id: "blank",
    name: "Blank",
    widgets: [],
  },
  {
    id: "haruquant",
    name: "HaruQuant",
    workspaceName: "HaruQuant",
    widgets: [
      // 12 columns x 26 rows: equal thirds left-to-right; the left column
      // stacks Markets/Calendar/Positions and the middle column stacks
      // Chart/Orders at different split points, with a full-height DOM.
      { type: "markets", title: "Markets", col: 1, row: 1, colSpan: 4, rowSpan: 8 },
      { type: "tradePlan", title: "Calendar", col: 1, row: 9, colSpan: 4, rowSpan: 9 },
      { type: "chart", title: "EURUSD Chart", symbol: "EURUSD", col: 5, row: 1, colSpan: 4, rowSpan: 17 },
      { type: "positions", title: "Positions", col: 1, row: 18, colSpan: 4, rowSpan: 9 },
      { type: "tradeLog", title: "Orders", col: 5, row: 18, colSpan: 4, rowSpan: 9 },
      { type: "priceLadder", title: "EURUSD DOM", symbol: "EURUSD", col: 9, row: 1, colSpan: 4, rowSpan: 26 },
    ],
  },
  {
    id: "chart-ladder",
    name: "Chart + Ladder",
    workspaceName: "Chart + Ladder",
    widgets: [
      // 12 columns x 25 rows: 24/51/24 column split; Markets and Calendar
      // halve the left column while the chart and DOM run full height.
      { type: "markets", title: "Markets", col: 1, row: 1, colSpan: 3, rowSpan: 12 },
      { type: "tradePlan", title: "Calendar", col: 1, row: 13, colSpan: 3, rowSpan: 13 },
      { type: "chart", title: "EURUSD Chart", symbol: "EURUSD", col: 4, row: 1, colSpan: 6, rowSpan: 25 },
      { type: "priceLadder", title: "EURUSD DOM", symbol: "EURUSD", col: 10, row: 1, colSpan: 3, rowSpan: 25 },
    ],
  },
  {
    id: "multicharts-ladder",
    name: "MultiCharts + Ladder",
    workspaceName: "MultiCharts + Ladder",
    widgets: [
      // 20 columns x 8 rows: rows at 24/26/50 of the height. The two chart
      // rows quarter the width; the ladder row fifths it (hence 20 columns).
      // Row 1 (top): 3 Charts + 1 Calendar
      { type: "chart", title: "EURUSD Chart", symbol: "EURUSD", col: 1, row: 1, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "GBPUSD Chart", symbol: "GBPUSD", col: 6, row: 1, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "USDJPY Chart", symbol: "USDJPY", col: 11, row: 1, colSpan: 5, rowSpan: 2 },
      { type: "tradePlan", title: "Calendar", col: 16, row: 1, colSpan: 5, rowSpan: 2 },
      // Row 2 (middle): 3 Charts + 1 Positions
      { type: "chart", title: "XAUUSD Chart", symbol: "XAUUSD", col: 1, row: 3, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "AUDUSD Chart", symbol: "AUDUSD", col: 6, row: 3, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "USDCHF Chart", symbol: "USDCHF", col: 11, row: 3, colSpan: 5, rowSpan: 2 },
      { type: "positions", title: "Positions & Orders", col: 16, row: 3, colSpan: 5, rowSpan: 2 },
      // Row 3 (bottom, double height): 5 equal Price Ladders
      { type: "priceLadder", title: "EURUSD DOM", symbol: "EURUSD", col: 1, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "priceLadder", title: "GBPUSD DOM", symbol: "GBPUSD", col: 5, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "priceLadder", title: "USDJPY DOM", symbol: "USDJPY", col: 9, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "priceLadder", title: "XAUUSD DOM", symbol: "XAUUSD", col: 13, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "priceLadder", title: "AUDUSD DOM", symbol: "AUDUSD", col: 17, row: 5, colSpan: 4, rowSpan: 4 },
    ],
  },
  {
    id: "options",
    name: "Options",
    workspaceName: "Options",
    widgets: [
      // 12 columns x 23 rows: equal halves; the options chain runs full
      // height while Markets (61%) and Positions (39%) halve the left side.
      { type: "markets", title: "Markets", col: 1, row: 1, colSpan: 6, rowSpan: 14 },
      { type: "optionsGrid", title: "EURUSD Options", symbol: "EURUSD", col: 7, row: 1, colSpan: 6, rowSpan: 23 },
      { type: "positions", title: "Positions & Orders", col: 1, row: 15, colSpan: 6, rowSpan: 9 },
    ],
  },
  {
    id: "charts",
    name: "Charts",
    workspaceName: "Charts",
    widgets: [
      // 12 columns x 2 rows: an even 2x4 chart grid.
      // Row 1 (top): 4 Charts
      { type: "chart", title: "EURUSD Chart", symbol: "EURUSD", col: 1, row: 1, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "GBPUSD Chart", symbol: "GBPUSD", col: 4, row: 1, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "USDJPY Chart", symbol: "USDJPY", col: 7, row: 1, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "XAUUSD Chart", symbol: "XAUUSD", col: 10, row: 1, colSpan: 3, rowSpan: 1 },
      // Row 2 (bottom): 4 Charts
      { type: "chart", title: "AUDUSD Chart", symbol: "AUDUSD", col: 1, row: 2, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "USDCHF Chart", symbol: "USDCHF", col: 4, row: 2, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "USDCAD Chart", symbol: "USDCAD", col: 7, row: 2, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "NZDUSD Chart", symbol: "NZDUSD", col: 10, row: 2, colSpan: 3, rowSpan: 1 },
    ],
  },
];

/**
 * Look up a template by id.
 *
 * @param id Template identifier.
 * @returns The registered template, or undefined for an unknown id (FR-UI-199 rejects those).
 */
export function findWorkspaceTemplate(id: string): WorkspaceTemplate | undefined {
  return WORKSPACE_TEMPLATES.find((template) => template.id === id);
}
