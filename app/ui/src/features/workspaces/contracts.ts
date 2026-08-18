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
  "marketTicks",
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
  "simulator",
  "risk",
  "trading",
  "sessions",
  "indicators",
  "news",
  "market-hours",
] as const;

export type WidgetType = (typeof WIDGET_TYPES)[number];

export interface Widget {
  id: string;
  type: WidgetType;
  title: string;
  symbol?: string;
  /** Real Trading account identifier, for widgets that read or submit real orders. */
  accountId?: string;
  /**
   * Legacy grid-rectangle coordinates. Used only to seed docking layout
   * proportions (FR-UI-201); live layout geometry is owned by the serialized
   * docking tree on the workspace.
   */
  col?: number;
  row?: number;
  colSpan?: number;
  rowSpan?: number;
}

export interface Workspace {
  id: number;
  name: string;
  expandedWidgetId: string | null;
  widgets: Widget[];
  /**
   * Serialized Dockview layout tree for this workspace (FR-UI-201). Opaque to
   * the store: the docking host produces and consumes it. Absent on legacy
   * layouts, which migrate deterministically on first open.
   */
  dock?: unknown;
  /**
   * True while a newly created workspace is still waiting for its template
   * choice (FR-UI-195); the grid renders the template picker instead of the
   * widget grid. Optional so pre-template persisted layouts keep validating.
   */
  templateChoicePending?: boolean;
}

export interface GridRect {
  col: number;
  row: number;
  colSpan: number;
  rowSpan: number;
}

/**
 * Application-wide account mode (FR-UI-016).
 *
 * `sim` executes virtually against the Simulator; `demo` and `live` both relay
 * to the connected MT5 terminal and differ only by the credentials the
 * operator supplied, so the app-level distinction is registry marking rather
 * than a technical gate. The operator elects the mode from the profile
 * dropdown and it persists as the `ACCOUNT_MODE` system setting (FR-UI-017).
 * `'unknown'` is the pre-resolution state and fails closed (FR-UI-021).
 */
export type AccountMode = "sim" | "demo" | "live" | "unknown";

/** Provider-authored execution mode, unresolved until account evidence loads. */
export type PlatformAccountMode = "sim" | "demo" | "live" | "contest" | "unknown";

/** The three selectable modes, in presentation order. */
export const SELECTABLE_ACCOUNT_MODES = ["sim", "demo", "live"] as const;

/** One operator-selectable account mode, excluding the unresolved state. */
export type SelectableAccountMode = (typeof SELECTABLE_ACCOUNT_MODES)[number];

/** Backend `ACCOUNT_MODE` system-setting key; the app-wide mode is stored here. */
export const ACCOUNT_MODE_SETTING_KEY = "ACCOUNT_MODE";

/**
 * Narrow an arbitrary stored value to a selectable account mode.
 *
 * The backend manifest constrains what can be written, so an unrecognized
 * value means the record predates the setting; it is refused rather than
 * coerced, leaving the mode unresolved (FR-UI-021).
 */
export function isSelectableAccountMode(value: unknown): value is SelectableAccountMode {
  return typeof value === "string" && (SELECTABLE_ACCOUNT_MODES as readonly string[]).includes(value);
}

/** Order-confirmation presentation mode (FR-UI-011). Always resets to `true` per session. */
export type ConfirmationMode = boolean;

/** Bounded custom workspace count (FR-UI-002). */
export const MAX_CUSTOM_WORKSPACES = 10;

export const widgetSchema: z.ZodType<Widget> = z.object({
  id: z.string().min(1),
  type: z.enum(WIDGET_TYPES),
  title: z.string(),
  symbol: z.string().optional(),
  accountId: z.string().optional(),
  col: z.number().optional(),
  row: z.number().optional(),
  colSpan: z.number().optional(),
  rowSpan: z.number().optional(),
});

export const workspaceSchema: z.ZodType<Workspace> = z.object({
  id: z.number(),
  name: z.string().min(1),
  expandedWidgetId: z.string().nullable(),
  widgets: z.array(widgetSchema),
  dock: z.unknown().optional(),
  templateChoicePending: z.boolean().optional(),
});

/** Shape of the slice persisted to `localStorage` - layout only (FR-UI-009/027). */
export const persistedLayoutSchema = z.object({
  workspaces: z.array(workspaceSchema).min(1),
  activeWorkspaceId: z.number(),
  defaultWorkspaceId: z.number(),
});

export type PersistedLayout = z.infer<typeof persistedLayoutSchema>;
