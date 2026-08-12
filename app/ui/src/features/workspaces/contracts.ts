/**
 * Workspace and widget layout contracts (FEAT-UI-01).
 *
 * `Widget`/`WidgetType`/`Workspace`/`GridRect` are UI-only presentation state -
 * never API contracts. The zod schemas exist solely to validate JSON recovered
 * from `localStorage` on rehydrate (FR-UI-010); they are not used for any
 * network traffic.
 */

import { z } from "zod";

export const WIDGET_TYPES = [
  "markets",
  "watchlist",
  "chart",
  "priceLadder",
  "optionsGrid",
  "positions",
  "tradeLog",
  "tradePlan",
  "education",
  "challenges",
  "dashboard",
  "data",
  "strategies",
  "research",
  "optimization",
  "portfolio",
  "agentic",
  "simulation",
  "risk",
  "trading",
  "indicators",
] as const;

export type WidgetType = (typeof WIDGET_TYPES)[number];

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

/** Live/simulation account mode (FR-UI-016). Never client-elected; `'unknown'` fails closed. */
export type AccountMode = "live" | "simulation" | "unknown";

/** Order-confirmation presentation mode (FR-UI-011). Always resets to `true` per session. */
export type ConfirmationMode = boolean;

/** Bounded custom workspace count (FR-UI-002). */
export const MAX_CUSTOM_WORKSPACES = 10;

export const widgetSchema: z.ZodType<Widget> = z.object({
  id: z.string().min(1),
  type: z.enum(WIDGET_TYPES),
  title: z.string(),
  symbol: z.string().optional(),
  col: z.number().optional(),
  row: z.number().optional(),
  colSpan: z.number(),
  rowSpan: z.number(),
});

export const workspaceSchema: z.ZodType<Workspace> = z.object({
  id: z.number(),
  name: z.string().min(1),
  expandedWidgetId: z.string().nullable(),
  widgets: z.array(widgetSchema),
});

/** Shape of the slice persisted to `localStorage` - layout only (FR-UI-009/027). */
export const persistedLayoutSchema = z.object({
  workspaces: z.array(workspaceSchema).min(1),
  activeWorkspaceId: z.number(),
  defaultWorkspaceId: z.number(),
});

export type PersistedLayout = z.infer<typeof persistedLayoutSchema>;
