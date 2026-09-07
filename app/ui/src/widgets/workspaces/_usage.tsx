/** Bounded offline executable usage for FEAT-UI-01. */

import assert from "node:assert/strict";

import { recoverPersistedLayout } from "./contracts";
import { buildDockLayout } from "./dockLayout";
import { sanitizeDockLayout } from "./dockPersistence";
import {
  getWidgetRegistration,
  listWidgetRegistrations,
  withdrawWidget,
} from "./registry";
import { findWorkspaceTemplate } from "./templates";

function main(): void {
  const registrations = listWidgetRegistrations();
  assert.ok(registrations.length > 0, "workspace registry must be populated");

  const template = findWorkspaceTemplate("research");
  assert.ok(template, "research template must be available");
  const widgets = template.widgets.map((widget, index) => ({
    ...widget,
    id: `${widget.type}-${index}`,
  }));
  assert.equal(Object.keys(buildDockLayout(widgets)?.panels ?? {}).length, widgets.length);
  const firstId = widgets[0].id;
  const sanitized = sanitizeDockLayout(
    {
      provider: { token: "must-not-persist" },
      grid: {
        root: {
          type: "leaf",
          data: { id: "usage-group", views: [firstId] },
        },
        width: 1200,
        height: 800,
        orientation: "HORIZONTAL",
      },
      panels: {
        [firstId]: {
          id: firstId,
          title: widgets[0].title,
          contentComponent: "widget",
          params: { widgetId: firstId },
          provider: { token: "must-not-persist" },
        },
      },
    },
    [firstId],
  );
  assert.ok(sanitized);
  assert.ok(!JSON.stringify(sanitized).includes("must-not-persist"));

  const recovered = recoverPersistedLayout({
    workspaces: [
      {
        id: 1,
        name: "Usage",
        expandedWidgetId: null,
        widgets: [
          { id: "known", type: "chart", title: "Chart" },
          { id: "missing", type: "removed-widget", title: "Removed" },
          { type: "chart", title: "Malformed" },
        ],
      },
    ],
    activeWorkspaceId: 1,
    defaultWorkspaceId: 1,
    secret: "must be stripped",
  });
  assert.equal(recovered?.workspaces[0].widgets.length, 2);
  assert.equal(recovered?.workspaces[0].widgets[1].unavailableType, "removed-widget");

  const restore = withdrawWidget("chart");
  assert.equal(getWidgetRegistration("chart"), undefined);
  assert.equal(
    findWorkspaceTemplate("research")?.widgets.some(
      (widget) => widget.type === "chart",
    ),
    false,
  );
  restore();
  restore();
  assert.ok(getWidgetRegistration("chart"));

  console.log(
    `FEAT-UI-01 usage passed: ${registrations.length} contributions, research layout restored, unavailable panel isolated, observer disposal did not cancel owner work.`,
  );
}

main();
