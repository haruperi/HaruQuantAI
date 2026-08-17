/**
 * Workspace layout and session-mode store (FEAT-UI-01).
 *
 * Owns non-authoritative workspace/widget layout, order-confirmation
 * presentation mode, and the app-wide account mode (sim/demo/live). Only
 * layout (`workspaces`, `activeWorkspaceId`, `defaultWorkspaceId`) persists to
 * `localStorage` (FR-UI-009); confirmation mode and account mode are session
 * state that is never inherited across a reload (FR-UI-012, FR-UI-027) - the
 * backend's `ACCOUNT_MODE` system setting is the authority for the mode and is
 * re-read every session.
 * Live layout geometry lives in each workspace's serialized Dockview tree
 * (`dock`, FR-UI-201); the widget list is the panel registry.
 */

import { create } from "zustand";
import { createJSONStorage, persist, type StateStorage } from "zustand/middleware";

import {
  MAX_CUSTOM_WORKSPACES,
  persistedLayoutSchema,
  type AccountMode,
  type PlatformAccountMode,
  type Widget,
  type WidgetType,
  type Workspace,
} from "./contracts";
import { buildDockLayout } from "./dockLayout";
import { findWorkspaceTemplate, type WorkspaceTemplateId } from "./templates";

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

/**
 * Maps the backend's `runtime_profile` to the app-wide account mode.
 *
 * The backend derives `runtime_profile` from the same `ACCOUNT_MODE` setting
 * the operator selects, so this is a vocabulary translation, not a guess:
 * Trading names the virtual profile `simulation` where the route and the
 * account mode both name it `sim`. A `research` deployment has no execution
 * route, so it resolves to the virtual mode. Anything unrecognized stays
 * `unknown` and fails closed (FR-UI-021).
 */
export function mapRuntimeProfileToAccountMode(profile?: string): AccountMode {
  switch (profile) {
    case "live":
      return "live";
    case "demo":
      return "demo";
    case "simulation":
    case "research":
      return "sim";
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

  // Application-wide account mode. Never persisted client-side: the backend's
  // ACCOUNT_MODE system setting is authoritative and is re-read every session
  // (FR-UI-027).
  accountMode: AccountMode;
  // Version of the system-settings record the mode was read from, required by
  // the backend's optimistic locking on write. -1 means "not yet read".
  accountModeVersion: number;
  platformAccountMode: PlatformAccountMode;
  tradingModeCompatible: boolean;
  marketDataDelaySeconds?: number;

  // Workspace actions
  setActiveWorkspace: (id: number) => void;
  setDefaultWorkspace: (id: number) => void;
  renameWorkspace: (id: number, name: string) => void;
  duplicateWorkspace: (id: number) => void;
  deleteWorkspace: (id: number) => void;
  addWorkspace: () => void;
  applyWorkspaceTemplate: (templateId: WorkspaceTemplateId) => void;
  /** Persist the docking host's serialized layout for one workspace (FR-UI-201). */
  setWorkspaceDockLayout: (workspaceId: number, layout: unknown) => void;

  // Widget registry actions
  expandWidget: (widgetId: string | null) => void;
  contractWidget: () => void;
  toggleExpandWidget: (widgetId: string | null) => void;
  switchExpandedWidget: (widgetId: string) => void;
  addWidgetToWorkspace: (widgetType: WidgetType, customTitle?: string, symbol?: string) => void;
  setWidgetSymbol: (widgetId: string, symbol: string) => void;
  removeWidget: (widgetId: string) => void;

  // Order-confirmation actions
  setOrderConfirmationRequired: (required: boolean) => void;
  toggleOrderConfirmation: () => void;

  // Account-mode actions (FR-UI-016/017/203)
  /** Apply the mode the authenticated session reports (`runtime_profile`). */
  setAccountModeFromRuntimeProfile: (profile?: string) => void;
  /**
   * Apply the mode read from, or written to, the ACCOUNT_MODE system setting.
   *
   * The caller owns the network round trip; this records the outcome so every
   * consumer of the store observes one app-wide mode. `'unknown'` is accepted
   * so a refused write can fail closed back to the unresolved state rather
   * than leaving a mode the backend is not routing to (FR-UI-021).
   */
  applyAccountMode: (mode: AccountMode, version: number) => void;
  applyPlatformAccountMode: (mode: PlatformAccountMode, compatible: boolean) => void;
}

/** True whenever account mode is unresolved - order entry must fail closed (FR-UI-021). */
export const selectOrderEntryDisabled = (state: WorkspaceStoreState): boolean =>
  state.accountMode === "unknown" || !state.tradingModeCompatible;

/** True unless fresh provider evidence exactly matches the elected mode. */
export const selectTradingActivityDisabled = selectOrderEntryDisabled;

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
      accountModeVersion: -1,
      platformAccountMode: "unknown",
      tradingModeCompatible: false,
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
          const widgets = source.widgets.map((widget) => ({
            ...widget,
            id: `${widget.type}-${newId}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          }));
          // The serialized tree references widget ids, so it is rebuilt for the
          // copied ids rather than cloned (FR-UI-025).
          const copy: Workspace = {
            ...source,
            id: newId,
            name: `${source.name} Copy`,
            expandedWidgetId: null,
            widgets,
            dock: buildDockLayout(widgets) ?? undefined,
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

      /**
       * Create a workspace pending its template choice (FR-UI-195): the new
       * workspace is deterministically named (FR-UI-003), opens empty, and is
       * flagged so the grid renders the template picker instead of widgets.
       */
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
            widgets: [],
            expandedWidgetId: null,
            templateChoicePending: true,
          };
          return { workspaces: [...state.workspaces, newWs], activeWorkspaceId: newId };
        }),

      /**
       * Apply a workspace template to the active workspace (FR-UI-196/197).
       *
       * Content templates replace the widget set with the template's preset,
       * rename the workspace to the template name, and seed a proportional
       * docking layout from the preset (FR-UI-201); Blank keeps the
       * deterministic name and empties the workspace. Unregistered ids are
       * rejected without any state change (FR-UI-199).
       */
      applyWorkspaceTemplate: (templateId) =>
        set((state) => {
          const template = findWorkspaceTemplate(templateId);
          const activeWs = state.workspaces.find((ws) => sameId(ws.id, state.activeWorkspaceId));
          if (!template || !activeWs) return state;

          const stamp = Date.now();
          const widgets: Widget[] = template.widgets.map((preset, index) => ({
            id: `${preset.type}-${activeWs.id}-${stamp}-${index}`,
            type: preset.type,
            title: preset.title,
            symbol: preset.symbol,
            col: preset.col,
            row: preset.row,
            colSpan: preset.colSpan,
            rowSpan: preset.rowSpan,
          }));

          return {
            workspaces: state.workspaces.map((ws) =>
              sameId(ws.id, state.activeWorkspaceId)
                ? {
                    ...ws,
                    widgets,
                    dock: buildDockLayout(widgets) ?? undefined,
                    name: template.workspaceName ?? ws.name,
                    templateChoicePending: false,
                  }
                : ws
            ),
          };
        }),

      /**
       * Record the docking host's serialized layout (FR-UI-201). Identical
       * layouts are ignored so restore-triggered layout-change events cannot
       * feed back into new state.
       */
      setWorkspaceDockLayout: (workspaceId, layout) =>
        set((state) => {
          const target = state.workspaces.find((ws) => sameId(ws.id, workspaceId));
          if (!target) return state;
          if (JSON.stringify(target.dock) === JSON.stringify(layout)) return state;
          return {
            workspaces: state.workspaces.map((ws) =>
              sameId(ws.id, workspaceId) ? { ...ws, dock: layout } : ws
            ),
          };
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

      addWidgetToWorkspace: (widgetType, customTitle, symbol = "EURUSD") =>
        set((state) => ({
          workspaces: state.workspaces.map((ws) => {
            if (!sameId(ws.id, state.activeWorkspaceId)) return ws;
            const newWidget: Widget = {
              id: `${widgetType}-${Date.now()}`,
              type: widgetType,
              title: customTitle || widgetType,
              symbol,
            };
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
            sameId(ws.id, state.activeWorkspaceId)
              ? { ...ws, widgets: ws.widgets.filter((w) => !sameId(w.id, widgetId)) }
              : ws
          ),
        })),

      setOrderConfirmationRequired: (required) => set({ orderConfirmationRequired: required }),
      toggleOrderConfirmation: () => set((state) => ({ orderConfirmationRequired: !state.orderConfirmationRequired })),

      setAccountModeFromRuntimeProfile: (profile) => set({ accountMode: mapRuntimeProfileToAccountMode(profile) }),
      applyAccountMode: (mode, version) => set({ accountMode: mode, accountModeVersion: version }),
      applyPlatformAccountMode: (mode, compatible) => set({
        platformAccountMode: mode,
        tradingModeCompatible: compatible,
      }),
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
