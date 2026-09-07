/** Requirement-mapped acceptance tests for FEAT-UI-01. */

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { getDomainGroups } from "../../../components/layout/Sidebar";
import { WidgetContentHost } from "../../../components/layout/WidgetContentHost";
import {
  DEFAULT_WORKSPACE_LAYOUT_CONFIG,
  resolveWorkspaceLayoutConfig,
} from "../config";
import {
  recoverPersistedLayout,
  WIDGET_TYPES,
  type Widget,
} from "../contracts";
import { buildDockLayout } from "../dockLayout";
import {
  getWidgetRegistration,
  listWidgetRegistrations,
  registerWidget,
  withdrawWidget,
} from "../registry";
import { findWorkspaceTemplate, WORKSPACE_TEMPLATES } from "../templates";

afterEach(cleanup);

describe("FEAT-UI-01 traceability", () => {
  it("test_trc_host_workspace_001", () => {
    const registrations = listWidgetRegistrations();
    expect(registrations.map((value) => value.manifest.widgetType)).toEqual(
      WIDGET_TYPES,
    );
    expect(
      registrations.map((value) => value.manifest.availability),
    ).toEqual(WIDGET_TYPES.map(() => "AVAILABLE"));
    expect(
      registrations.map((value) => value.manifest.qualification.status),
    ).toEqual(WIDGET_TYPES.map(() => "UNQUALIFIED"));
    expect(
      registrations
        .filter((value) =>
          value.manifest.qualification.kind.startsWith("legacy-"),
        )
        .map((value) => value.manifest.qualification.ownerId)
        .filter((value) => value.startsWith("FEAT-UI-"))
        .sort(),
    ).toEqual(
      [
        "FEAT-UI-02",
        "FEAT-UI-03",
        "FEAT-UI-05",
        "FEAT-UI-06",
        "FEAT-UI-08",
        "FEAT-UI-09",
        "FEAT-UI-10",
        "FEAT-UI-11",
        "FEAT-UI-12",
        "FEAT-UI-19",
        "FEAT-UI-25",
        "FEAT-UI-26",
        "FEAT-UI-29",
        "FEAT-UI-30",
      ].sort(),
    );
    expect(
      getWidgetRegistration("dashboard")?.manifest.qualification,
    ).toMatchObject({ kind: "planned-feature", ownerId: "FEAT-UI-16" });
    expect(
      getWidgetRegistration("risk")?.manifest.qualification,
    ).toMatchObject({
      kind: "legacy-surface",
      ownerId: "components/workflow/risk",
    });
    expect(
      getWidgetRegistration("markets")?.manifest.declaredManifest?.effects.network,
    ).toBe(true);
    expect(
      getDomainGroups().flatMap((domain) => domain.items)
        .flatMap((item) => (item.type === undefined ? [] : [item.type]))
        .sort(),
    ).toEqual([...WIDGET_TYPES].sort());
    const restore = withdrawWidget("markets");
    expect(
      getDomainGroups().flatMap((domain) => domain.items).some(
        (item) => item.type === "markets",
      ),
    ).toBe(false);
    expect(findWorkspaceTemplate("haruquant")?.widgets.some(
      (widget) => widget.type === "markets",
    )).toBe(false);
    restore();
    for (const template of WORKSPACE_TEMPLATES) {
      expect(
        findWorkspaceTemplate(template.id)?.widgets.every(
          (widget) => getWidgetRegistration(widget.type) !== undefined,
        ),
      ).toBe(true);
    }
  });

  it("test_trc_host_workspace_002", () => {
    const recovered = recoverPersistedLayout({
      workspaces: [
        {
          id: 7,
          name: "Recovered",
          expandedWidgetId: null,
          widgets: [
            { id: "valid", type: "markets", title: "Markets", secret: "removed" },
            { id: "missing", type: "removed-widget", title: "Unavailable" },
            { id: "bad", type: "chart" },
          ],
          dock: {
            provider: { token: "SECRET" },
            grid: {
              width: 1200,
              height: 800,
              orientation: "HORIZONTAL",
              root: {
                type: "leaf",
                data: { id: "main", views: ["valid"], activeView: "valid" },
              },
            },
            panels: {
              valid: {
                id: "valid",
                title: "Markets",
                contentComponent: "widget",
                params: { widgetId: "valid" },
                provider: { token: "SECRET" },
              },
            },
          },
          provider: { token: "removed" },
        },
      ],
      activeWorkspaceId: 7,
      defaultWorkspaceId: 7,
      strategy: { source: "removed" },
    });

    expect(recovered?.workspaces[0].widgets).toHaveLength(2);
    expect(recovered?.workspaces[0].widgets[0]).toEqual({
      id: "valid",
      type: "markets",
      title: "Markets",
    });
    expect(recovered?.workspaces[0].widgets[1].unavailableType).toBe("removed-widget");
    expect(recovered).not.toHaveProperty("strategy");
    expect(recovered?.workspaces[0]).not.toHaveProperty("provider");
    expect(JSON.stringify(recovered?.workspaces[0].dock)).not.toContain("SECRET");
  });

  it("test_trc_host_workspace_003", () => {
    const research = findWorkspaceTemplate("research");
    expect(research?.name).toBe("Research");
    const layout = buildDockLayout(
      (research?.widgets ?? []).map((widget, index): Widget => ({
        ...widget,
        id: `${widget.type}-${index}`,
      })),
    );
    expect(Object.keys(layout?.panels ?? {})).toHaveLength(3);
    expect(DEFAULT_WORKSPACE_LAYOUT_CONFIG.allowCrossWindowPopout).toBe(false);
    expect(DEFAULT_WORKSPACE_LAYOUT_CONFIG).not.toHaveProperty("saveDebounceMs");
    expect(() =>
      resolveWorkspaceLayoutConfig({ saveDebounceMs: 0 }),
    ).toThrow();
  });

  it("test_trc_host_workspace_004", async () => {
    const original = getWidgetRegistration("markets");
    if (original === undefined) throw new Error("markets registration missing");
    const disposeObserver = vi.fn();
    const cancelOwnerJob = vi.fn();
    const unregister = registerWidget("markets", {
      ...original,
      load: async () => ({ default: () => <div>Scoped observer</div> }),
      createScope: () => disposeObserver,
    });

    const view = render(
      <WidgetContentHost widget={{ id: "observer", type: "markets", title: "Markets" }} />,
    );
    await screen.findByText("Scoped observer");
    view.unmount();
    await waitFor(() => expect(disposeObserver).toHaveBeenCalledTimes(1));
    expect(cancelOwnerJob).not.toHaveBeenCalled();
    unregister();
  });
});
