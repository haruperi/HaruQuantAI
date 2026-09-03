/**
 * Phase 5 spatial proof for the Market Ticks vertical slice:
 * workspace add/remove, serialization round-trip, and the explicit
 * missing-widget behavior when the contribution is physically absent.
 */
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { WidgetContentHost } from "../../components/layout/WidgetContentHost";
import { widgetSchema, type Widget } from "../workspaces/contracts";
import { useWorkspaceStore } from "../workspaces/store";

describe("FEAT-UI-25 spatial evidence — Phase 5", () => {
  beforeEach(() => {
    useWorkspaceStore.setState({
      workspaces: [
        {
          id: 1,
          name: "Default",
          expandedWidgetId: null,
          widgets: [],
        },
      ],
      activeWorkspaceId: 1,
      orderConfirmationRequired: true,
      accountMode: "sim",
    });
  });

  it("adds and removes the market ticks widget in a workspace", () => {
    const store = useWorkspaceStore.getState();
    store.addWidgetToWorkspace("marketTicks", "Market Ticks");

    let workspace = useWorkspaceStore
      .getState()
      .workspaces.find((candidate) => candidate.id === 1)!;
    const added = workspace.widgets.find(
      (widget) => widget.type === "marketTicks",
    );
    expect(added).toBeDefined();
    expect(added?.title).toBe("Market Ticks");

    useWorkspaceStore.getState().removeWidget(added!.id);
    workspace = useWorkspaceStore
      .getState()
      .workspaces.find((candidate) => candidate.id === 1)!;
    expect(
      workspace.widgets.some((widget) => widget.type === "marketTicks"),
    ).toBe(false);
  });

  it("survives workspace serialization and restore", () => {
    useWorkspaceStore.getState().addWidgetToWorkspace("marketTicks");

    const workspace = useWorkspaceStore
      .getState()
      .workspaces.find((candidate) => candidate.id === 1)!;
    // The persistence path serializes each widget through the strict
    // schema and rehydrates it on restore (FR-UI-009/010).
    const serialized = JSON.stringify(workspace.widgets);
    const restored = (JSON.parse(serialized) as unknown[]).map((entry) =>
      widgetSchema.parse(entry),
    ) as Widget[];

    expect(restored).toHaveLength(1);
    expect(restored[0].type).toBe("marketTicks");
  });

  it("renders the explicit missing-widget state for an unregistered contribution", () => {
    // A saved workspace may outlive the physical widget feature: the
    // persisted type has no registered contribution in this build. The
    // host must say so explicitly instead of substituting another widget.
    const ghost = {
      id: "ghost-1",
      type: "marketTicksRemoved",
      title: "Market Ticks",
    } as unknown as Widget;

    render(<WidgetContentHost widget={ghost} />);

    const missing = screen.getByRole("status");
    expect(missing).toHaveTextContent("marketTicksRemoved");
    expect(missing).toHaveTextContent("not registered in this build");
    expect(screen.queryByText("Latest quotes")).not.toBeInTheDocument();
  });
});
