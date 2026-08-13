/**
 * Unit tests for the FEAT-UI-01 workspace/session-mode store, mapped to
 * FR-UI-001 through FR-UI-029 in `app/ui/README.md` §4.1.
 */

import { beforeEach, describe, expect, it } from "vitest";

import { useWorkspaceStore, selectOrderEntryDisabled, mapRuntimeProfileToAccountMode } from "./store";
import { MAX_CUSTOM_WORKSPACES, persistedLayoutSchema, widgetSchema } from "./contracts";

const initialState = useWorkspaceStore.getState();

beforeEach(() => {
  useWorkspaceStore.setState(initialState, true);
  // This jsdom environment doesn't always expose window.localStorage; the
  // store's own storage wrapper already tolerates its absence (store.ts),
  // and none of the tests below round-trip through the real backing store.
  window.localStorage?.clear();
});

describe("FR-UI-001 default workspace", () => {
  it("provides at least one workspace with the registered widget set on first load", () => {
    const { workspaces, defaultWorkspaceId } = useWorkspaceStore.getState();
    expect(workspaces.length).toBeGreaterThan(0);
    expect(workspaces.some((ws) => ws.id === defaultWorkspaceId)).toBe(true);
    expect(workspaces[0].widgets.length).toBeGreaterThan(0);
  });
});

describe("FR-UI-002/003 bounded creation with deterministic naming", () => {
  it("names the first created workspace New Workspace-2 (seed already has -1)", () => {
    useWorkspaceStore.getState().addWorkspace();
    const names = useWorkspaceStore.getState().workspaces.map((w) => w.name);
    expect(names).toContain("New Workspace-2");
  });

  it("rejects creation beyond the bounded maximum", () => {
    for (let i = 0; i < MAX_CUSTOM_WORKSPACES + 5; i++) {
      useWorkspaceStore.getState().addWorkspace();
    }
    expect(useWorkspaceStore.getState().workspaces.length).toBe(MAX_CUSTOM_WORKSPACES);
  });
});

describe("FR-UI-004 rename/duplicate/delete", () => {
  it("renames a workspace, trimming whitespace and ignoring blank input", () => {
    useWorkspaceStore.getState().renameWorkspace(1, "  My Workspace  ");
    expect(useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)?.name).toBe("My Workspace");

    useWorkspaceStore.getState().renameWorkspace(1, "   ");
    expect(useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)?.name).toBe("My Workspace");
  });

  it("duplicates a workspace with a fresh id and widget ids, preserving widget content", () => {
    const before = useWorkspaceStore.getState().workspaces.length;
    useWorkspaceStore.getState().duplicateWorkspace(1);
    const state = useWorkspaceStore.getState();
    expect(state.workspaces.length).toBe(before + 1);
    const copy = state.workspaces[state.workspaces.length - 1];
    expect(copy.name).toBe("HaruQuantAI Workspace Copy");
    expect(copy.widgets.map((w) => w.type)).toEqual(state.workspaces[0].widgets.map((w) => w.type));
    expect(copy.widgets.every((w) => !state.workspaces[0].widgets.some((orig) => orig.id === w.id))).toBe(true);
  });

  it("rejects deleting the last remaining workspace", () => {
    const state = useWorkspaceStore.getState();
    const ids = state.workspaces.map((w) => w.id);
    for (const id of ids.slice(0, -1)) {
      useWorkspaceStore.getState().deleteWorkspace(id);
    }
    expect(useWorkspaceStore.getState().workspaces.length).toBe(1);
    const lastId = useWorkspaceStore.getState().workspaces[0].id;
    useWorkspaceStore.getState().deleteWorkspace(lastId);
    expect(useWorkspaceStore.getState().workspaces.length).toBe(1);
  });
});

describe("FR-UI-005 default workspace designation", () => {
  it("allows designating a different workspace as default", () => {
    useWorkspaceStore.getState().setDefaultWorkspace(2);
    expect(useWorkspaceStore.getState().defaultWorkspaceId).toBe(2);
  });
});

describe("FR-UI-006/025 reorder preserves widget identity", () => {
  it("swaps rectangles between two widgets while keeping their ids", () => {
    useWorkspaceStore.getState().reorderWidgets("markets-1", "chart-1");
    const ws = useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!;
    expect(ws.widgets.map((w) => w.id)).toEqual(["markets-1", "chart-1", "ladder-1", "positions-1"]);
    const markets = ws.widgets.find((w) => w.id === "markets-1")!;
    const chart = ws.widgets.find((w) => w.id === "chart-1")!;
    expect(markets.col).toBe(7); // took chart's original position
    expect(chart.col).toBe(1); // took markets' original position
  });
});

describe("FR-UI-008 expand/contract retains the prior rectangle", () => {
  it("does not mutate a widget's rect on expand or contract", () => {
    const before = useWorkspaceStore
      .getState()
      .workspaces.find((w) => w.id === 1)!
      .widgets.find((w) => w.id === "markets-1")!;

    useWorkspaceStore.getState().expandWidget("markets-1");
    expect(useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!.expandedWidgetId).toBe("markets-1");

    useWorkspaceStore.getState().contractWidget();
    const after = useWorkspaceStore
      .getState()
      .workspaces.find((w) => w.id === 1)!
      .widgets.find((w) => w.id === "markets-1")!;

    expect(useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!.expandedWidgetId).toBeNull();
    expect(after).toEqual(before);
  });
});

describe("FR-UI-009/027 persistence scope", () => {
  it("persists only workspace layout, never account/order/confirmation/mode state", () => {
    const options = useWorkspaceStore.persist.getOptions();
    const persisted = options.partialize!(useWorkspaceStore.getState()) as Record<string, unknown>;
    expect(Object.keys(persisted).sort()).toEqual(["activeWorkspaceId", "defaultWorkspaceId", "workspaces"]);
  });
});

describe("FR-UI-010 corrupt persisted layout falls back to default", () => {
  it("returns the current (default) state unchanged when persisted JSON fails schema validation", () => {
    const options = useWorkspaceStore.persist.getOptions();
    const current = useWorkspaceStore.getState();

    expect(options.merge!({ garbage: true }, current)).toBe(current);
    expect(options.merge!(null, current)).toBe(current);
    expect(options.merge!(undefined, current)).toBe(current);
    expect(options.merge!({ workspaces: "not-an-array" }, current)).toBe(current);
  });

  it("accepts well-formed persisted layout", () => {
    const options = useWorkspaceStore.persist.getOptions();
    const current = useWorkspaceStore.getState();
    const validPayload = {
      workspaces: [{ id: 9, name: "Restored", expandedWidgetId: null, widgets: [] }],
      activeWorkspaceId: 9,
      defaultWorkspaceId: 9,
    };
    const merged = options.merge!(validPayload, current);
    expect(merged.workspaces).toEqual(validPayload.workspaces);
    expect(merged.activeWorkspaceId).toBe(9);
  });

  it("the persisted-layout schema rejects malformed shapes directly", () => {
    expect(persistedLayoutSchema.safeParse({ workspaces: [] }).success).toBe(false); // min(1)
    expect(persistedLayoutSchema.safeParse("not json shape").success).toBe(false);
    expect(
      persistedLayoutSchema.safeParse({
        workspaces: [{ id: 1, name: "A", expandedWidgetId: null, widgets: [] }],
        activeWorkspaceId: 1,
        defaultWorkspaceId: 1,
      }).success
    ).toBe(true);
  });
});

describe("FR-UI-011/012 order-confirmation mode", () => {
  it("defaults to confirmation-required and is not persisted", () => {
    expect(useWorkspaceStore.getState().orderConfirmationRequired).toBe(true);
    const options = useWorkspaceStore.persist.getOptions();
    const persisted = options.partialize!(useWorkspaceStore.getState());
    expect(persisted).not.toHaveProperty("orderConfirmationRequired");
  });

  it("can be disabled and re-enabled", () => {
    useWorkspaceStore.getState().setOrderConfirmationRequired(false);
    expect(useWorkspaceStore.getState().orderConfirmationRequired).toBe(false);
    useWorkspaceStore.getState().toggleOrderConfirmation();
    expect(useWorkspaceStore.getState().orderConfirmationRequired).toBe(true);
  });
});

describe("FR-UI-016/017 account mode derivation", () => {
  it("maps the backend runtime_profile to the presentation account mode", () => {
    expect(mapRuntimeProfileToAccountMode("live")).toBe("live");
    expect(mapRuntimeProfileToAccountMode("simulation")).toBe("simulation");
    expect(mapRuntimeProfileToAccountMode("paper")).toBe("simulation");
    expect(mapRuntimeProfileToAccountMode("research")).toBe("simulation");
    expect(mapRuntimeProfileToAccountMode("something-else")).toBe("unknown");
    expect(mapRuntimeProfileToAccountMode(undefined)).toBe("unknown");
  });

  it("defaults to unknown and is only ever changed via setAccountModeFromRuntimeProfile", () => {
    expect(useWorkspaceStore.getState().accountMode).toBe("unknown");
    useWorkspaceStore.getState().setAccountModeFromRuntimeProfile("live");
    expect(useWorkspaceStore.getState().accountMode).toBe("live");
    useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(undefined);
    expect(useWorkspaceStore.getState().accountMode).toBe("unknown");
  });

  it("is not persisted - every session re-derives it from the live identity", () => {
    useWorkspaceStore.getState().setAccountModeFromRuntimeProfile("live");
    const options = useWorkspaceStore.persist.getOptions();
    const persisted = options.partialize!(useWorkspaceStore.getState());
    expect(persisted).not.toHaveProperty("accountMode");
  });
});

describe("FR-UI-021 fail-closed order entry", () => {
  it("disables order entry exactly when account mode is unknown", () => {
    expect(selectOrderEntryDisabled(useWorkspaceStore.getState())).toBe(true);
    useWorkspaceStore.getState().setAccountModeFromRuntimeProfile("simulation");
    expect(selectOrderEntryDisabled(useWorkspaceStore.getState())).toBe(false);
    useWorkspaceStore.getState().setAccountModeFromRuntimeProfile("live");
    expect(selectOrderEntryDisabled(useWorkspaceStore.getState())).toBe(false);
  });
});

describe("FR-UI-023 widget type is from the registered set only", () => {
  it("accepts a registered widget type and rejects an unregistered one", () => {
    const base = { id: "w-1", title: "Markets", colSpan: 6, rowSpan: 2 };
    expect(widgetSchema.safeParse({ ...base, type: "markets" }).success).toBe(true);
    expect(widgetSchema.safeParse({ ...base, type: "not-a-real-widget" }).success).toBe(false);
  });
});

describe("FR-UI-024 rectangle bounds", () => {
  it("moveWidgetToCell clamps a destination beyond the grid back onto it", () => {
    // A large row keeps the destination free of the other seed widgets, so the
    // move actually happens and the clamp on `col` is what's being verified.
    useWorkspaceStore.getState().moveWidgetToCell("markets-1", 999, 50);
    const widget = useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!.widgets.find((w) => w.id === "markets-1")!;
    expect(widget.row).toBe(50);
    expect(widget.col).toBe(7); // clamped to GRID_COLUMNS(12) - colSpan(6) + 1
  });

  it("moveWidgetToCell rejects a destination already occupied", () => {
    const before = useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!.widgets.find((w) => w.id === "markets-1")!;
    // chart-1 occupies col 7, row 1 - moving markets-1 exactly there should be a no-op.
    useWorkspaceStore.getState().moveWidgetToCell("markets-1", 7, 1);
    const after = useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!.widgets.find((w) => w.id === "markets-1")!;
    expect(after.col).toBe(before.col);
    expect(after.row).toBe(before.row);
  });

  it("resizeWidget clamps span to the 12-column grid and registered maximum", () => {
    // Clear the siblings first so growth isn't itself rejected for colliding
    // with a neighbour - this test is specifically about the span clamp.
    useWorkspaceStore.getState().removeWidget("chart-1");
    useWorkspaceStore.getState().removeWidget("ladder-1");
    useWorkspaceStore.getState().removeWidget("positions-1");
    useWorkspaceStore.getState().resizeWidget("markets-1", 999, 999);
    const widget = useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!.widgets.find((w) => w.id === "markets-1")!;
    expect(widget.colSpan).toBe(12); // GRID_COLUMNS - col(1) + 1
    expect(widget.rowSpan).toBe(6); // MAX_ROW_SPAN
  });
});

describe("FR-UI-026 empty workspace presents explicitly", () => {
  it("removing every widget leaves an explicit empty array, not undefined", () => {
    const ws = useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!;
    for (const widget of [...ws.widgets]) {
      useWorkspaceStore.getState().removeWidget(widget.id);
    }
    expect(useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!.widgets).toEqual([]);
  });
});

describe("FR-UI-029 no fixture data", () => {
  it("imports nothing from the mock fixtures directory", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const dir = path.join(process.cwd(), "src", "features", "workspaces");
    const storeSource = fs.readFileSync(path.join(dir, "store.ts"), "utf-8");
    const contractsSource = fs.readFileSync(path.join(dir, "contracts.ts"), "utf-8");
    expect(storeSource).not.toMatch(/from ['"].*\/mock\//);
    expect(contractsSource).not.toMatch(/from ['"].*\/mock\//);
  });
});

describe("symbol-bound widget headings follow the charted symbol", () => {
  it("retitles and repoints a chart widget when its symbol changes", () => {
    useWorkspaceStore.getState().setWidgetSymbol("chart-1", "GBPJPY");

    const widget = useWorkspaceStore
      .getState()
      .workspaces.find((w) => w.id === 1)!
      .widgets.find((w) => w.id === "chart-1")!;

    expect(widget.symbol).toBe("GBPJPY");
    expect(widget.title).toBe("GBPJPY Chart");
  });

  it("normalizes case and whitespace, and ignores a blank symbol", () => {
    useWorkspaceStore.getState().setWidgetSymbol("chart-1", "  gbpusd  ");
    const after = () =>
      useWorkspaceStore.getState().workspaces.find((w) => w.id === 1)!
        .widgets.find((w) => w.id === "chart-1")!;
    expect(after().symbol).toBe("GBPUSD");

    useWorkspaceStore.getState().setWidgetSymbol("chart-1", "   ");
    expect(after().symbol).toBe("GBPUSD");
    expect(after().title).toBe("GBPUSD Chart");
  });

  it("applies each widget type's own naming convention", () => {
    useWorkspaceStore.getState().setWidgetSymbol("ladder-1", "NQZ5");
    const widget = useWorkspaceStore
      .getState()
      .workspaces.find((w) => w.id === 1)!
      .widgets.find((w) => w.id === "ladder-1")!;
    expect(widget.title).toBe("NQZ5 DOM");
  });

  it("never overwrites a title the user chose rather than the convention", () => {
    useWorkspaceStore.setState((state) => ({
      workspaces: state.workspaces.map((ws) =>
        ws.id === 1
          ? {
              ...ws,
              widgets: ws.widgets.map((w) =>
                w.id === "chart-1" ? { ...w, title: "Morning scalps" } : w
              ),
            }
          : ws
      ),
    }));

    useWorkspaceStore.getState().setWidgetSymbol("chart-1", "GBPJPY");

    const widget = useWorkspaceStore
      .getState()
      .workspaces.find((w) => w.id === 1)!
      .widgets.find((w) => w.id === "chart-1")!;
    expect(widget.title).toBe("Morning scalps");
    expect(widget.symbol).toBe("GBPJPY");
  });

  it("leaves a widget with no symbol convention untouched", () => {
    useWorkspaceStore.getState().setWidgetSymbol("positions-1", "EURUSD");
    const widget = useWorkspaceStore
      .getState()
      .workspaces.find((w) => w.id === 1)!
      .widgets.find((w) => w.id === "positions-1")!;
    expect(widget.title).toBe("Positions & Orders");
    expect(widget.symbol).toBe("EURUSD");
  });
});
