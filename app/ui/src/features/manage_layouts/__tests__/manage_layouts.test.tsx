import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import {
  parseManageLayoutsConfig,
  MANAGE_LAYOUTS_TEMPLATES,
  findManageLayoutsTemplate,
  buildTemplateManager,
  createLayoutPersistence,
  truncatePlacements,
  clampScale,
  MIN_SCALE,
  MAX_SCALE,
  ViewScaleProvider,
  ScaleControls,
  createFeature,
} from "../index";
// jsdom in this configuration exposes no localStorage; provide an
// in-memory Storage stub so persistence tests exercise the real code path.
if (typeof window !== "undefined" && !window.localStorage) {
  const store = new Map<string, string>();
  const stub: Storage = {
    get length() {
      return store.size;
    },
    key: (i) => Array.from(store.keys())[i] ?? null,
    getItem: (k) => (store.has(k) ? store.get(k)! : null),
    setItem: (k, v) => void store.set(k, String(v)),
    removeItem: (k) => void store.delete(k),
    clear: () => void store.clear(),
  };
  Object.defineProperty(window, "localStorage", { value: stub, configurable: true });
}
import type { WorkspaceLayoutSnapshot } from "../../../contracts/generated/ui";
import type { IUiPresentationClient } from "../../../clients/ui_client";

function makeSnapshot(instanceCount: number): WorkspaceLayoutSnapshot {
  return {
    layout_id: `layout-test-${instanceCount}`,
    workspace_id: "ws-test",
    actor_id: "actor-default",
    layout_version: 1,
    capability_snapshot_id: "snap-test",
    widget_instances: Array.from({ length: instanceCount }, (_, i) => ({
      instance_id: `inst-${i}`,
      widget_type: "system_status",
      workspace_id: "ws-test",
      configuration_version: 1,
      state_version: 1,
      schema_version: 1 as const,
    })),
    placements: Array.from({ length: instanceCount }, (_, i) => ({
      instance_id: `inst-${i}`,
      panel_id: `panel-${Math.floor(i / 2)}`,
      panel_order: Math.floor(i / 2),
      tab_order: i % 2,
      size_ratio: "1",
      schema_version: 1 as const,
    })),
    active_panel_id: "inst-0",
    content_hash: `hash-${instanceCount}`,
    schema_version: 1,
  };
}

describe("FEAT-UI-MANAGE_LAYOUTS config", () => {
  it("provides strict defaults and rejects unknown keys", () => {
    const defaults = parseManageLayoutsConfig();
    expect(defaults.maxRestoredTabs).toBe(20);
    expect(defaults.layoutSchemaVersion).toBe(1);
    expect(parseManageLayoutsConfig({ max_restored_tabs: 5 }).maxRestoredTabs).toBe(5);
    expect(() => parseManageLayoutsConfig({ unknown_key: 1 })).toThrow(/Unknown configuration keys/);
  });
});

describe("FEAT-UI-MANAGE_LAYOUTS templates (FR-UI-COMPOSE_PANELS)", () => {
  it("converts the five harvested donor presets into valid versioned templates", () => {
    expect(MANAGE_LAYOUTS_TEMPLATES).toHaveLength(5);
    const chartLadder = findManageLayoutsTemplate("template-chart-ladder-v1")!;
    expect(chartLadder).toBeDefined();
    expect(chartLadder!.name).toBe("Chart + Ladder");
    // Guillotine conversion: 3 column clusters -> 3 panel groups.
    const placements = chartLadder!.layout.placements ?? [];
    const panelIds = new Set(placements.map((p) => p.panel_id));
    expect(panelIds.size).toBe(3);
    // Every instance has a placement and sizes sum to ~1.
    const totalRatio = placements
      .filter((p) => p.tab_order === 0)
      .reduce((acc, p) => acc + Number(p.size_ratio), 0);
    expect(totalRatio).toBeCloseTo(1, 5);
  });

  it("registers harvested templates on a TemplateManager for the engine", () => {
    const manager = buildTemplateManager();
    const instantiated = manager.instantiateTemplate(
      "template-charts-v1",
      "ws-test"
    );
    expect(instantiated.workspace_id).toBe("ws-test");
    expect(instantiated.widget_instances).toHaveLength(8);
  });
});

describe("FEAT-UI-PERSIST_LAYOUTS / FR-UI-RESTORE_LAYOUTS persistence", () => {
  it("round-trips a snapshot through bounded storage and clears dirty state", () => {
    const persistence = createLayoutPersistence({
      schemaVersion: 1,
      maxRestoredTabs: 20,
    });
    persistence.save("ws-a", makeSnapshot(3));
    const result = persistence.load("ws-a");
    expect(result.snapshot).not.toBeNull();
    expect(result.snapshot!.widget_instances).toHaveLength(3);
    expect(result.diagnostics).toHaveLength(0);
    persistence.clear("ws-a");
    expect(persistence.load("ws-a").snapshot).toBeNull();
  });

  it("discards snapshots from a different schema version with an explicit diagnostic", () => {
    const v1 = createLayoutPersistence({ schemaVersion: 1, maxRestoredTabs: 20 });
    const v2 = createLayoutPersistence({ schemaVersion: 2, maxRestoredTabs: 20 });
    v1.save("ws-b", makeSnapshot(2));
    const result = v2.load("ws-b");
    expect(result.snapshot).toBeNull();
    expect(result.diagnostics[0].code).toBe("NO_PERSISTED_LAYOUT");
  });

  it("discards corrupt snapshots deterministically", () => {
    window.localStorage.setItem(
      "haruquantai.layout.v1.actor-default.ws-c",
      "{not-json"
    );
    const persistence = createLayoutPersistence({ schemaVersion: 1, maxRestoredTabs: 20 });
    const result = persistence.load("ws-c");
    expect(result.snapshot).toBeNull();
    expect(result.diagnostics[0].code).toBe("CORRUPT_SNAPSHOT");
  });

  it("FR-UI-MANAGE_TABS: truncates restored placements to max restored tabs", () => {
    const { snapshot, truncated } = truncatePlacements(makeSnapshot(25), 20);
    expect(truncated).toBe(true);
    expect(snapshot.widget_instances).toHaveLength(20);
    expect(snapshot.placements).toHaveLength(20);
    const notTruncated = truncatePlacements(makeSnapshot(10), 20);
    expect(notTruncated.truncated).toBe(false);
  });
});

describe("FR-UI-SCALE_VIEWS scale controls", () => {
  it("clamps zoom to the documented bounds so safety state stays visible", () => {
    expect(clampScale(0.1)).toBe(MIN_SCALE);
    expect(clampScale(9)).toBe(MAX_SCALE);
    expect(clampScale(1.25)).toBe(1.25);
  });

  it("renders header zoom/fullscreen controls with bounded zoom steps", () => {
    const unused = async () => {
      throw new Error("unused");
    };
    const client = { isDevOnly: true, manageLayouts: unused } as unknown as IUiPresentationClient;
    const feature = createFeature({ presentationClient: client });
    expect(feature.manifest.featureId).toBe("FEAT-UI-MANAGE_LAYOUTS");
    expect(feature.manifest.providesCapabilities).toContain("ui.manage-layouts@1");

    render(
      <ViewScaleProvider>
        <ScaleControls />
      </ViewScaleProvider>
    );

    expect(screen.getByTestId("scale-zoom-in")).toBeInTheDocument();
    expect(screen.getByTestId("scale-zoom-out")).toBeInTheDocument();
    expect(screen.getByTestId("scale-fullscreen")).toBeInTheDocument();
    expect(screen.getByTestId("scale-reset").textContent).toBe("100%");

    fireEvent.click(screen.getByTestId("scale-zoom-in"));
    expect(screen.getByTestId("scale-reset").textContent).toBe("125%");
    // Bounded: repeated zoom-in saturates at MAX_SCALE.
    fireEvent.click(screen.getByTestId("scale-zoom-in"));
    fireEvent.click(screen.getByTestId("scale-zoom-in"));
    fireEvent.click(screen.getByTestId("scale-zoom-in"));
    expect(screen.getByTestId("scale-reset").textContent).toBe("150%");
    cleanup();
  });
});
