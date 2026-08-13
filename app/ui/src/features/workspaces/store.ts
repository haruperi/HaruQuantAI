/**
 * Workspace layout and session-mode store (FEAT-UI-01).
 *
 * Owns non-authoritative workspace/widget layout, order-confirmation
 * presentation mode, and live/simulation account-mode presentation. Only
 * layout (`workspaces`, `activeWorkspaceId`, `defaultWorkspaceId`) persists to
 * `localStorage` (FR-UI-009); confirmation mode and account mode are session
 * state that is never inherited across a reload (FR-UI-012, FR-UI-027).
 */

import { create } from "zustand";
import { createJSONStorage, persist, type StateStorage } from "zustand/middleware";

import {
  GRID_COLUMNS,
  MIN_COL_SPAN,
  MAX_COL_SPAN,
  MIN_ROW_SPAN,
  MAX_ROW_SPAN,
  rectOf,
  isAreaFree,
  findFreeCell,
} from "../../utils/gridLayout";
import {
  MAX_CUSTOM_WORKSPACES,
  persistedLayoutSchema,
  type AccountMode,
  type Widget,
  type WidgetType,
  type Workspace,
} from "./contracts";

/** Loose id comparison replaced with an explicit string coercion everywhere. */
const sameId = (a: string | number, b: string | number | null): boolean => String(a) === String(b);

/**
 * Title convention for widgets whose heading names the instrument they show.
 *
 * These match the seeded widget titles exactly, which is what lets
 * `setWidgetSymbol` tell a conventional title apart from a custom one.
 */
const SYMBOL_TITLE_SUFFIX: Partial<Record<WidgetType, string>> = {
  chart: "Chart",
  priceLadder: "DOM",
  optionsGrid: "Options",
};

/** Maps the backend's `runtime_profile` to the UI's account-mode presentation. Never guesses. */
export function mapRuntimeProfileToAccountMode(profile?: string): AccountMode {
  switch (profile) {
    case "live":
      return "live";
    case "simulation":
    case "paper":
    case "research":
      return "simulation";
    default:
      return "unknown";
  }
}

const DEFAULT_WORKSPACES: Workspace[] = [
  {
    id: 1,
    name: "HaruQuantAI Workspace",
    expandedWidgetId: null,
    widgets: [
      { id: "markets-1", type: "markets", title: "Markets", col: 1, row: 1, colSpan: 6, rowSpan: 2 },
      { id: "chart-1", type: "chart", title: "EURUSD Chart", symbol: "EURUSD", col: 7, row: 1, colSpan: 6, rowSpan: 2 },
      { id: "ladder-1", type: "priceLadder", title: "ESU5 DOM", symbol: "ESU5", col: 1, row: 3, colSpan: 4, rowSpan: 2 },
      { id: "positions-1", type: "positions", title: "Positions & Orders", col: 5, row: 3, colSpan: 8, rowSpan: 2 },
    ],
  },
  {
    id: 2,
    name: "New Workspace-1",
    expandedWidgetId: null,
    widgets: [
      { id: "watchlist-1", type: "watchlist", title: "Watchlist", col: 1, row: 1, colSpan: 6, rowSpan: 2 },
      { id: "options-1", type: "optionsGrid", title: "ESU5 Options", symbol: "ESU5", col: 7, row: 1, colSpan: 6, rowSpan: 2 },
      { id: "data-1", type: "data", title: "Data Capabilities", col: 1, row: 3, colSpan: 12, rowSpan: 3 },
    ],
  },
];

export interface WorkspaceStoreState {
  // Workspace layout (persisted)
  workspaces: Workspace[];
  activeWorkspaceId: number;
  defaultWorkspaceId: number;

  // Order-confirmation presentation mode (session-only)
  orderConfirmationRequired: boolean;

  // Account mode presentation (session-only, API-derived)
  accountMode: AccountMode;
  marketDataDelaySeconds?: number;

  // Workspace actions
  setActiveWorkspace: (id: number) => void;
  setDefaultWorkspace: (id: number) => void;
  renameWorkspace: (id: number, name: string) => void;
  duplicateWorkspace: (id: number) => void;
  deleteWorkspace: (id: number) => void;
  addWorkspace: () => void;

  // Widget layout actions
  expandWidget: (widgetId: string | null) => void;
  contractWidget: () => void;
  toggleExpandWidget: (widgetId: string | null) => void;
  switchExpandedWidget: (widgetId: string) => void;
  reorderWidgets: (sourceWidgetId: string, targetWidgetId: string) => void;
  moveWidgetToCell: (widgetId: string, col: number, row: number) => void;
  resizeWidget: (widgetId: string, colSpan: number, rowSpan: number) => void;
  addWidgetToWorkspace: (widgetType: WidgetType, customTitle?: string, symbol?: string) => void;
  setWidgetSymbol: (widgetId: string, symbol: string) => void;
  removeWidget: (widgetId: string) => void;

  // Order-confirmation actions
  setOrderConfirmationRequired: (required: boolean) => void;
  toggleOrderConfirmation: () => void;

  // Account-mode actions - the only legal writer of `accountMode` (FR-UI-017)
  setAccountModeFromRuntimeProfile: (profile?: string) => void;
}

/** True whenever account mode is unresolved - order entry must fail closed (FR-UI-021). */
export const selectOrderEntryDisabled = (state: WorkspaceStoreState): boolean =>
  state.accountMode === "unknown";

/** localStorage wrapper that never throws and never returns unparsable JSON. */
const safeStorage: StateStorage = {
  getItem: (name) => {
    if (typeof window === "undefined") return null;
    try {
      const raw = window.localStorage.getItem(name);
      if (raw === null) return null;
      JSON.parse(raw);
      return raw;
    } catch {
      return null;
    }
  },
  setItem: (name, value) => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(name, value);
    } catch {
      // Storage may be unavailable (private mode, quota); layout preference is lost, not fatal.
    }
  },
  removeItem: (name) => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.removeItem(name);
    } catch {
      // Best-effort clear.
    }
  },
};

export const useWorkspaceStore = create<WorkspaceStoreState>()(
  persist(
    (set) => ({
      workspaces: DEFAULT_WORKSPACES,
      activeWorkspaceId: 1,
      defaultWorkspaceId: 1,

      orderConfirmationRequired: true,

      accountMode: "unknown",
      marketDataDelaySeconds: undefined,

      setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),

      setDefaultWorkspace: (id) => set({ defaultWorkspaceId: id }),

      renameWorkspace: (id, name) =>
        set((state) => ({
          workspaces: state.workspaces.map((ws) =>
            sameId(ws.id, id) ? { ...ws, name: name.trim() || ws.name } : ws
          ),
        })),

      duplicateWorkspace: (id) =>
        set((state) => {
          const source = state.workspaces.find((ws) => sameId(ws.id, id));
          if (!source || state.workspaces.length >= MAX_CUSTOM_WORKSPACES) return state;
          const newId = Math.max(...state.workspaces.map((ws) => Number(ws.id) || 0)) + 1;
          const copy: Workspace = {
            ...source,
            id: newId,
            name: `${source.name} Copy`,
            expandedWidgetId: null,
            widgets: source.widgets.map((widget) => ({
              ...widget,
              id: `${widget.type}-${newId}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            })),
          };
          return { workspaces: [...state.workspaces, copy], activeWorkspaceId: newId };
        }),

      deleteWorkspace: (id) =>
        set((state) => {
          if (state.workspaces.length <= 1) return state;
          const remaining = state.workspaces.filter((ws) => !sameId(ws.id, id));
          const nextActive = sameId(state.activeWorkspaceId, id) ? remaining[0].id : state.activeWorkspaceId;
          const nextDefault = sameId(state.defaultWorkspaceId, id) ? remaining[0].id : state.defaultWorkspaceId;
          return { workspaces: remaining, activeWorkspaceId: nextActive, defaultWorkspaceId: nextDefault };
        }),

      addWorkspace: () =>
        set((state) => {
          if (state.workspaces.length >= MAX_CUSTOM_WORKSPACES) return state;

          let maxNum = 0;
          state.workspaces.forEach((ws) => {
            const match = ws.name.match(/^New Workspace-(\d+)$/i);
            if (match) {
              const num = parseInt(match[1], 10);
              if (num > maxNum) maxNum = num;
            }
          });
          const nextNum = maxNum + 1;
          const newId = Date.now();
          const newWs: Workspace = {
            id: newId,
            name: `New Workspace-${nextNum}`,
            widgets: [
              { id: `markets-${newId}`, type: "markets", title: "Markets", colSpan: 6, rowSpan: 2 },
              { id: `chart-${newId}`, type: "chart", title: "EURUSD Chart", symbol: "EURUSD", colSpan: 6, rowSpan: 2 },
            ],
            expandedWidgetId: null,
          };
          return { workspaces: [...state.workspaces, newWs], activeWorkspaceId: newId };
        }),

      expandWidget: (widgetId) =>
        set((state) => {
          const activeWs = state.workspaces.find((ws) => sameId(ws.id, state.activeWorkspaceId)) || state.workspaces[0];
          const targetId = widgetId || activeWs?.widgets[0]?.id || null;
          return {
            workspaces: state.workspaces.map((ws) =>
              sameId(ws.id, state.activeWorkspaceId) ? { ...ws, expandedWidgetId: targetId } : ws
            ),
          };
        }),

      contractWidget: () =>
        set((state) => ({
          workspaces: state.workspaces.map((ws) =>
            sameId(ws.id, state.activeWorkspaceId) ? { ...ws, expandedWidgetId: null } : ws
          ),
        })),

      toggleExpandWidget: (widgetId) =>
        set((state) => {
          const activeWs = state.workspaces.find((ws) => sameId(ws.id, state.activeWorkspaceId)) || state.workspaces[0];
          const isCurrentlyExpanded = Boolean(activeWs?.expandedWidgetId);
          const targetId = widgetId || activeWs?.widgets[0]?.id || null;
          return {
            workspaces: state.workspaces.map((ws) =>
              sameId(ws.id, state.activeWorkspaceId)
                ? { ...ws, expandedWidgetId: isCurrentlyExpanded ? null : targetId }
                : ws
            ),
          };
        }),

      switchExpandedWidget: (widgetId) =>
        set((state) => ({
          workspaces: state.workspaces.map((ws) =>
            sameId(ws.id, state.activeWorkspaceId) ? { ...ws, expandedWidgetId: widgetId } : ws
          ),
        })),

      /**
       * Drop a widget onto another widget: the two exchange rectangles, so a
       * narrow widget dropped on a wide one grows to fill it. Nothing else moves.
       */
      reorderWidgets: (sourceWidgetId, targetWidgetId) =>
        set((state) => {
          const activeWs = state.workspaces.find((ws) => sameId(ws.id, state.activeWorkspaceId));
          if (!activeWs || !targetWidgetId || targetWidgetId === "END") return state;

          const widgets = [...activeWs.widgets];
          const sourceIdx = widgets.findIndex((w) => sameId(w.id, sourceWidgetId));
          const targetIdx = widgets.findIndex((w) => sameId(w.id, targetWidgetId));
          if (sourceIdx === -1 || targetIdx === -1 || sourceIdx === targetIdx) return state;

          const sourceRect = rectOf(widgets[sourceIdx]);
          const targetRect = rectOf(widgets[targetIdx]);

          widgets[sourceIdx] = { ...widgets[sourceIdx], ...targetRect };
          widgets[targetIdx] = { ...widgets[targetIdx], ...sourceRect };

          return {
            workspaces: state.workspaces.map((ws) => (sameId(ws.id, state.activeWorkspaceId) ? { ...ws, widgets } : ws)),
          };
        }),

      /**
       * Drop a widget onto empty canvas: it is pinned at those exact
       * coordinates and stays there. Out-of-bounds and occupied targets are
       * rejected outright (FR-UI-024) - the state is returned unchanged.
       */
      moveWidgetToCell: (widgetId, col, row) =>
        set((state) => {
          const activeWs = state.workspaces.find((ws) => sameId(ws.id, state.activeWorkspaceId));
          if (!activeWs) return state;

          const widget = activeWs.widgets.find((w) => sameId(w.id, widgetId));
          if (!widget) return state;

          const { colSpan, rowSpan } = rectOf(widget);
          const nextCol = Math.min(Math.max(col, 1), GRID_COLUMNS - colSpan + 1);
          const nextRow = Math.max(row, 1);

          if (widget.col === nextCol && widget.row === nextRow) return state;
          if (!isAreaFree(activeWs.widgets, { col: nextCol, row: nextRow, colSpan, rowSpan }, widgetId)) {
            return state;
          }

          return {
            workspaces: state.workspaces.map((ws) =>
              sameId(ws.id, state.activeWorkspaceId)
                ? { ...ws, widgets: ws.widgets.map((w) => (sameId(w.id, widgetId) ? { ...w, col: nextCol, row: nextRow } : w)) }
                : ws
            ),
          };
        }),

      /**
       * Resize a widget by corner drag or keyboard step. Spans are clamped to
       * the 12-column grid and the registered min/max spans; growing into an
       * occupied neighbour is rejected (FR-UI-024), shrinking always succeeds.
       */
      resizeWidget: (widgetId, colSpan, rowSpan) =>
        set((state) => {
          const activeWs = state.workspaces.find((ws) => sameId(ws.id, state.activeWorkspaceId));
          if (!activeWs) return state;

          const widget = activeWs.widgets.find((w) => sameId(w.id, widgetId));
          if (!widget) return state;

          const { col, row } = rectOf(widget);
          const nextColSpan = Math.min(Math.max(Math.round(colSpan), MIN_COL_SPAN), Math.min(MAX_COL_SPAN, GRID_COLUMNS - col + 1));
          const nextRowSpan = Math.min(Math.max(Math.round(rowSpan), MIN_ROW_SPAN), MAX_ROW_SPAN);

          if (widget.colSpan === nextColSpan && widget.rowSpan === nextRowSpan) return state;

          const grew = nextColSpan > (widget.colSpan || 6) || nextRowSpan > (widget.rowSpan || 2);
          if (grew && !isAreaFree(activeWs.widgets, { col, row, colSpan: nextColSpan, rowSpan: nextRowSpan }, widgetId)) {
            return state;
          }

          return {
            workspaces: state.workspaces.map((ws) =>
              sameId(ws.id, state.activeWorkspaceId)
                ? { ...ws, widgets: ws.widgets.map((w) => (sameId(w.id, widgetId) ? { ...w, colSpan: nextColSpan, rowSpan: nextRowSpan } : w)) }
                : ws
            ),
          };
        }),

      addWidgetToWorkspace: (widgetType, customTitle, symbol = "EURUSD") =>
        set((state) => ({
          workspaces: state.workspaces.map((ws) => {
            if (!sameId(ws.id, state.activeWorkspaceId)) return ws;
            const newWidgetId = `${widgetType}-${Date.now()}`;
            const cell = findFreeCell(ws.widgets, 6, 2);
            const newWidget: Widget = { id: newWidgetId, type: widgetType, title: customTitle || widgetType, symbol, ...cell, colSpan: 6, rowSpan: 2 };
            return { ...ws, widgets: [...ws.widgets, newWidget] };
          }),
        })),

      /**
       * Record the symbol a symbol-bound widget is currently showing.
       *
       * Widgets own their active symbol internally, so without this the stored
       * `symbol` and `title` keep describing whatever the widget was created
       * with — a chart moved to GBPJPY still reads "EURUSD Chart" and reopens
       * on EURUSD. The title is only regenerated while it still matches the
       * convention for the previous symbol, so a deliberately custom title
       * (see `addWidgetToWorkspace`) is never overwritten.
       */
      setWidgetSymbol: (widgetId, symbol) =>
        set((state) => {
          const next = symbol.trim().toUpperCase();
          if (!next) return state;

          const activeWs = state.workspaces.find((ws) => sameId(ws.id, state.activeWorkspaceId));
          const widget = activeWs?.widgets.find((w) => sameId(w.id, widgetId));
          if (!widget || widget.symbol === next) return state;

          const suffix = SYMBOL_TITLE_SUFFIX[widget.type];
          const retitle =
            suffix !== undefined && widget.title === `${widget.symbol} ${suffix}`;

          return {
            workspaces: state.workspaces.map((ws) =>
              sameId(ws.id, state.activeWorkspaceId)
                ? {
                    ...ws,
                    widgets: ws.widgets.map((w) =>
                      sameId(w.id, widgetId)
                        ? {
                            ...w,
                            symbol: next,
                            title: retitle ? `${next} ${suffix}` : w.title,
                          }
                        : w
                    ),
                  }
                : ws
            ),
          };
        }),

      removeWidget: (widgetId) =>
        set((state) => ({
          workspaces: state.workspaces.map((ws) =>
            sameId(ws.id, state.activeWorkspaceId) ? { ...ws, widgets: ws.widgets.filter((w) => w.id !== widgetId) } : ws
          ),
        })),

      setOrderConfirmationRequired: (required) => set({ orderConfirmationRequired: required }),
      toggleOrderConfirmation: () => set((state) => ({ orderConfirmationRequired: !state.orderConfirmationRequired })),

      setAccountModeFromRuntimeProfile: (profile) => set({ accountMode: mapRuntimeProfileToAccountMode(profile) }),
    }),
    {
      name: "hq:workspace-layout",
      storage: createJSONStorage(() => safeStorage),
      // Layout is the only client preference allowed to persist; confirmation
      // mode and account mode are session state (FR-UI-012, FR-UI-027).
      partialize: (state) => ({
        workspaces: state.workspaces,
        activeWorkspaceId: state.activeWorkspaceId,
        defaultWorkspaceId: state.defaultWorkspaceId,
      }),
      // Corrupt or wrong-shape persisted layout falls back to the in-code
      // default workspace rather than failing to render (FR-UI-010).
      merge: (persistedState, currentState) => {
        const parsed = persistedLayoutSchema.safeParse(persistedState);
        if (!parsed.success) return currentState;
        return { ...currentState, ...parsed.data };
      },
      version: 2,
    }
  )
);
