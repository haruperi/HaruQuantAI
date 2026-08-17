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

import type { Workspace } from "../../features/workspaces";
import { useWorkspaceStore } from "../../features/workspaces";
import type { Widget } from "../../features/workspaces";

const widget = (over: Partial<Widget> & Pick<Widget, "id" | "type" | "title">): Widget => ({
  ...over,
});

const makeApi = () => {
  const panels: {
    id: string;
    title: string;
    api: { close: ReturnType<typeof vi.fn>; setTitle: ReturnType<typeof vi.fn>; maximize: ReturnType<typeof vi.fn>; exitMaximized: ReturnType<typeof vi.fn>; isMaximized: () => boolean; moveTo: ReturnType<typeof vi.fn>; group: {} };
  }[] = [];
  const pushPanel = (id: string, title: string) => {
    const panel = {
      id,
      title,
      api: {
        close: vi.fn(),
        setTitle: vi.fn(),
        maximize: vi.fn(),
        exitMaximized: vi.fn(),
        isMaximized: () => false,
        moveTo: vi.fn(),
        group: {},
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
  DockviewReact: (props: { onReady: (event: { api: unknown }) => void }) => {
    useEffect(() => {
      props.onReady({ api: fakeApi });
    }, []);
    return <div data-testid="dockview" />;
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
      api: { close: vi.fn(), setTitle: vi.fn(), maximize: vi.fn(), exitMaximized: vi.fn(), isMaximized: () => false, moveTo: vi.fn(), group: {} },
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
      expect.objectContaining({ id: "b", position: { referencePanel: "a", direction: "within" } })
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
      api: { close: vi.fn(), setTitle: vi.fn(), maximize: vi.fn(), exitMaximized: vi.fn(), isMaximized: () => false, moveTo, group: { g: 1 } },
    };
    const shell = document.querySelector(".workspace-dock-shell") as HTMLElement;

    fireEvent.keyDown(shell, { key: "ArrowRight", altKey: true });
    expect(moveTo).toHaveBeenCalledWith({ group: { g: 1 }, position: "right" });

    fireEvent.keyDown(shell, { key: "ArrowRight" });
    expect(moveTo).toHaveBeenCalledTimes(1);
  });
});

afterEach(cleanup);
