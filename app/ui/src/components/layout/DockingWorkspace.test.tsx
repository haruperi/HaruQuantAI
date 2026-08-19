/**
 * Component tests for the docking workspace host (FEAT-UI-01/16,
 * FR-UI-006/007/008/201 in `app/ui/README.md` §4.1 and §4.16).
 *
 * Dockview itself is mocked: these tests verify the adapter's restore,
 * reconciliation, persistence, and keyboard behaviour against a fake API.
 */
import React, { useEffect } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render } from "@testing-library/react";

import type { Workspace } from "../../widgets/workspaces";
import { useWorkspaceStore } from "../../widgets/workspaces";
import type { Widget } from "../../widgets/workspaces";

const widget = (over: Partial<Widget> & Pick<Widget, "id" | "type" | "title">): Widget => ({
  ...over,
});

const makeApi = () => {
  const panels: {
    id: string;
    title: string;
    api: { close: ReturnType<typeof vi.fn>; setTitle: ReturnType<typeof vi.fn>; maximize: ReturnType<typeof vi.fn>; exitMaximized: ReturnType<typeof vi.fn>; isMaximized: () => boolean; moveTo: ReturnType<typeof vi.fn>; group: {}; location: { type: "grid" | "floating" } };
  }[] = [];
  const pushPanel = (id: string, title: string) => {
    let maximized = false;
    const panel = {
      id,
      title,
      api: {
        close: vi.fn(),
        setTitle: vi.fn(),
        maximize: vi.fn(() => { maximized = true; }),
        exitMaximized: vi.fn(() => { maximized = false; }),
        isMaximized: () => maximized,
        moveTo: vi.fn(),
        group: {},
        location: { type: "floating" as const },
      },
    };
    panels.push(panel);
    api.activePanel = panel;
    return panel;
  };
  const api = {
    panels,
    activePanel: undefined as (typeof panels)[number] | undefined,
    fromJSON: vi.fn((layout: { panels?: Record<string, { id: string; title?: string }> }) => {
      for (const state of Object.values(layout?.panels ?? {})) {
        pushPanel(state.id, state.title ?? state.id);
      }
    }),
    addPanel: vi.fn((options: { id: string; title: string }) => pushPanel(options.id, options.title)),
    getPanel: (id: string) => panels.find((panel) => panel.id === id),
    onDidRemovePanel: vi.fn(),
    onDidLayoutChange: vi.fn(),
    toJSON: vi.fn(() => ({ saved: true })),
  };
  return api;
};

const fakeApi = makeApi();

vi.mock("dockview-react", () => ({
  Orientation: { HORIZONTAL: "HORIZONTAL", VERTICAL: "VERTICAL" },
  DockviewReact: (props: {
    onReady: (event: { api: unknown }) => void;
    defaultTabComponent?: React.ComponentType<{
      api: {
        id: string;
        isMaximized: () => boolean;
        maximize: () => void;
        exitMaximized: () => void;
      };
    }>;
  }) => {
    useEffect(() => {
      props.onReady({ api: fakeApi });
    }, []);
    const Tab = props.defaultTabComponent;
    return (
      <div data-testid="dockview">
        <div className="dv-floating-overlay-host">
          <div className="dv-resize-container">
          {Tab && (
            <Tab
              api={{
                id: "a",
                isMaximized: () => fakeApi.getPanel("a")?.api.isMaximized() ?? false,
                maximize: () => fakeApi.getPanel("a")?.api.maximize(),
                exitMaximized: () => fakeApi.getPanel("a")?.api.exitMaximized(),
              }}
            />
          )}
          </div>
        </div>
      </div>
    );
  },
  DockviewDefaultTab: () => null,
}));

vi.mock("./WidgetContentHost", () => ({
  WidgetContentHost: () => <div />,
}));

import { DockingWorkspace } from "./DockingWorkspace";

const initialState = useWorkspaceStore.getState();

beforeEach(() => {
  useWorkspaceStore.setState(initialState, true);
  fakeApi.panels.length = 0;
  fakeApi.activePanel = undefined;
  fakeApi.fromJSON.mockClear();
  fakeApi.addPanel.mockClear();
  fakeApi.onDidLayoutChange.mockClear();
  fakeApi.onDidRemovePanel.mockClear();
  window.localStorage?.clear();
});

const workspaceWith = (widgets: Widget[], dock?: unknown): Workspace => ({
  id: 77,
  name: "Dock Test",
  expandedWidgetId: null,
  widgets,
  dock,
});

describe("FR-UI-201 restore path", () => {
  it("restores a persisted serialized layout instead of rebuilding", () => {
    const dock = { grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" }, panels: { a: { id: "a" } } };
    render(<DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], dock)} />);
    expect(fakeApi.fromJSON).toHaveBeenCalledWith(dock);
    expect(fakeApi.addPanel).not.toHaveBeenCalled();
  });

  it("falls back to the deterministic factory when no layout is saved", () => {
    render(<DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })])} />);
    expect(fakeApi.fromJSON).toHaveBeenCalledTimes(1);
    const layout = fakeApi.fromJSON.mock.calls[0][0] as { panels: Record<string, unknown> };
    expect(Object.keys(layout.panels)).toEqual(["a"]);
    expect(fakeApi.addPanel).not.toHaveBeenCalled();
  });

  it("subscribes layout changes to debounced persistence", () => {
    vi.useFakeTimers();
    try {
      // The adapter saves through the real store, so workspace 77 must exist there.
      act(() => {
        useWorkspaceStore.setState((state) => ({
          workspaces: [...state.workspaces, workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })])],
          activeWorkspaceId: 77,
        }));
      });
      const dock = { grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" }, panels: { a: { id: "a", title: "Markets" } } };
      render(<DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], dock)} />);
      expect(fakeApi.onDidLayoutChange).toHaveBeenCalledTimes(1);
      const emitChange = fakeApi.onDidLayoutChange.mock.calls[0][0] as () => void;
      // Let the restore window's save-suppression clear first.
      act(() => {
        vi.advanceTimersByTime(5);
      });
      act(() => {
        emitChange();
      });
      act(() => {
        vi.advanceTimersByTime(300);
      });
      const ws = useWorkspaceStore.getState().workspaces.find((w) => w.id === 77);
      expect(ws?.dock).toEqual({ saved: true });
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("registry reconciliation", () => {
  it("docks a newly added widget as a tab in the active group", () => {
    const dock = { grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" }, panels: { a: { id: "a" } } };
    const { rerender } = render(
      <DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], dock)} />
    );
    fakeApi.panels.push({
      id: "a",
      title: "Markets",
      api: { close: vi.fn(), setTitle: vi.fn(), maximize: vi.fn(), exitMaximized: vi.fn(), isMaximized: () => false, moveTo: vi.fn(), group: {}, location: { type: "floating" } },
    });
    rerender(
      <DockingWorkspace
        workspace={workspaceWith([
          widget({ id: "a", type: "markets", title: "Markets" }),
          widget({ id: "b", type: "chart", title: "EURUSD Chart" }),
        ])}
      />
    );
    expect(fakeApi.addPanel).toHaveBeenCalledWith(
      expect.objectContaining({ id: "b", floating: expect.objectContaining({ width: 580, height: 440 }) })
    );
  });

  it("closes the panel of a widget removed from the registry", () => {
    const dock = { grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" }, panels: { a: { id: "a", title: "Markets" } } };
    const { rerender } = render(
      <DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], dock)} />
    );
    const panel = fakeApi.getPanel("a");
    if (!panel) throw new Error("panel a was not restored");
    rerender(<DockingWorkspace workspace={workspaceWith([])} />);
    expect(panel.api.close).toHaveBeenCalled();
  });

  it("retitles a panel when the registry title changes", () => {
    const dock = { grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" }, panels: { a: { id: "a", title: "Markets" } } };
    const { rerender } = render(
      <DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], dock)} />
    );
    const panel = fakeApi.getPanel("a");
    if (!panel) throw new Error("panel a was not restored");
    rerender(
      <DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Renamed" })], dock)} />
    );
    expect(panel.api.setTitle).toHaveBeenCalledWith("Renamed");
  });
});

describe("FR-UI-007 keyboard panel moves", () => {
  it("moves the active panel with Alt+Arrow and ignores plain arrows", () => {
    const dock = { grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" }, panels: { a: { id: "a" } } };
    render(<DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], dock)} />);
    const moveTo = vi.fn();
    fakeApi.activePanel = {
      id: "a",
      title: "Markets",
      api: { close: vi.fn(), setTitle: vi.fn(), maximize: vi.fn(), exitMaximized: vi.fn(), isMaximized: () => false, moveTo, group: { g: 1 }, location: { type: "grid" } },
    };
    const shell = document.querySelector(".workspace-dock-shell") as HTMLElement;

    fireEvent.keyDown(shell, { key: "ArrowRight", altKey: true });
    expect(moveTo).toHaveBeenCalledWith({ group: { g: 1 }, position: "right" });

    fireEvent.keyDown(shell, { key: "ArrowRight" });
    expect(moveTo).toHaveBeenCalledTimes(1);
  });
});

describe("FR-UI-006/008 widget header drag handle and expansion control", () => {
  it("renders panel tabs with only the explicit Expand control", () => {
    const dock = { grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" }, panels: { a: { id: "a" } } };
    render(<DockingWorkspace workspace={workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], dock)} />);
    const tab = document.querySelector(".workspace-dock-tab");
    expect(tab).not.toBeNull();
    expect(tab?.className).toContain("widget-header-grab");
    expect(tab?.getAttribute("title")).toContain("drag tab header to move widget");

    const expandBtn = document.querySelector(".widget-header-expand-btn");
    const minimizeBtn = document.querySelector(".widget-header-minimize-btn");
    const closeBtn = document.querySelector(".widget-header-close-btn");
    expect(expandBtn).not.toBeNull();
    expect(minimizeBtn).toBeNull();
    expect(closeBtn).toBeNull();
  });

  it("expands a floating container from the title-bar control and restores its prior bounds", () => {
    const workspace = workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], {
      grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" },
      panels: { a: { id: "a" } },
    });
    act(() => {
      useWorkspaceStore.setState((state) => ({
        workspaces: [...state.workspaces, workspace],
        activeWorkspaceId: workspace.id,
      }));
    });
    render(<DockingWorkspace workspace={workspace} />);
    const panel = fakeApi.getPanel("a");
    if (!panel) throw new Error("panel a was not restored");

    fireEvent.click(document.querySelector(".widget-header-expand-btn") as HTMLButtonElement);
    expect(panel.api.maximize).not.toHaveBeenCalled();
    expect(document.querySelector(".dv-resize-container")).toHaveClass("workspace-floating-widget--expanded");
    expect(document.querySelector(".widget-header-expand-btn")).toHaveAttribute("aria-label", "Restore widget");

    fireEvent.click(document.querySelector(".widget-header-expand-btn") as HTMLButtonElement);
    expect(panel.api.exitMaximized).not.toHaveBeenCalled();
    expect(document.querySelector(".dv-resize-container")).not.toHaveClass("workspace-floating-widget--expanded");
    expect(document.querySelector(".widget-header-expand-btn")).toHaveAttribute("aria-label", "Expand widget");
  });

  it("keeps Dockview native maximize for docked groups", () => {
    const workspace = workspaceWith([widget({ id: "a", type: "markets", title: "Markets" })], {
      grid: { root: { type: "leaf" }, height: 1, width: 1, orientation: "VERTICAL" },
      panels: { a: { id: "a" } },
    });
    act(() => {
      useWorkspaceStore.setState((state) => ({
        workspaces: [...state.workspaces, workspace],
        activeWorkspaceId: workspace.id,
      }));
    });
    render(<DockingWorkspace workspace={workspace} />);
    const panel = fakeApi.getPanel("a");
    if (!panel) throw new Error("panel a was not restored");
    panel.api.location = { type: "grid" };
    document.querySelector(".dv-resize-container")?.classList.remove("dv-resize-container");

    fireEvent.click(document.querySelector(".widget-header-expand-btn") as HTMLButtonElement);
    expect(panel.api.maximize).toHaveBeenCalledTimes(1);
  });
});

afterEach(cleanup);
