/** Lifecycle and physical-removal acceptance tests for FEAT-UI-COMPOSE_WORKSPACE. */

import React, { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WidgetContentHost } from "../../../components/layout/WidgetContentHost";
import { recoverPersistedLayout } from "../contracts";
import {
  getWidgetRegistration,
  registerWidget,
  withdrawWidget,
} from "../registry";

describe("FEAT-UI-COMPOSE_WORKSPACE lifecycle", () => {
  it("test_trc_host_workspace_nfr_001", () => {
    const original = getWidgetRegistration("markets");
    if (original === undefined) throw new Error("markets registration missing");

    for (let cycle = 0; cycle < 100; cycle += 1) {
      const unregister = registerWidget("markets", original);
      unregister();
      unregister();
      expect(getWidgetRegistration("markets")).toBe(original);
    }

    const restore = withdrawWidget("markets");
    expect(getWidgetRegistration("markets")).toBeUndefined();
    render(
      <WidgetContentHost widget={{ id: "removed", type: "markets", title: "Markets" }} />,
    );
    expect(screen.getByRole("status", { name: "Missing widget: Markets" })).toHaveTextContent(
      "not registered",
    );
    restore();
    restore();
    expect(getWidgetRegistration("markets")).toBe(original);

    const recovered = recoverPersistedLayout({
      workspaces: [
        {
          id: 1,
          name: "Partial",
          expandedWidgetId: null,
          widgets: [
            { id: "kept", type: "chart", title: "Chart" },
            { type: "chart", title: "Malformed" },
          ],
        },
      ],
      activeWorkspaceId: 1,
      defaultWorkspaceId: 1,
    });
    expect(recovered?.workspaces[0].widgets.map((widget) => widget.id)).toEqual(["kept"]);
  });

  it("keeps one lazy component per registration generation", async () => {
    const original = getWidgetRegistration("markets");
    if (original === undefined) throw new Error("markets registration missing");
    const mounted = vi.fn();
    const unmounted = vi.fn();
    const First = (): React.JSX.Element => {
      useEffect(() => {
        mounted();
        return unmounted;
      }, []);
      return <p>First generation</p>;
    };
    const unregisterFirst = registerWidget("markets", {
      ...original,
      load: async () => ({ default: First }),
    });
    const view = render(
      <WidgetContentHost widget={{ id: "stable", type: "markets", title: "One" }} />,
    );
    await screen.findByText("First generation");
    view.rerender(
      <WidgetContentHost widget={{ id: "stable", type: "markets", title: "Two" }} />,
    );
    expect(mounted).toHaveBeenCalledTimes(1);
    expect(unmounted).not.toHaveBeenCalled();

    const unregisterSecond = registerWidget("markets", {
      ...original,
      load: async () => ({ default: () => <p>Second generation</p> }),
    });
    view.rerender(
      <WidgetContentHost widget={{ id: "stable", type: "markets", title: "Three" }} />,
    );
    await screen.findByText("Second generation");
    expect(unmounted).toHaveBeenCalledTimes(1);
    unregisterSecond();
    unregisterFirst();
  });
});
