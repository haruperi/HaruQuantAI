import { describe, it, expect } from "vitest";
import {
  computeContentHash,
  migrateLayout,
  restoreLayout,
} from "../layout_serializer";
import { WidgetRegistry } from "../../runtime/widget_registry";
import type { WorkspaceLayoutSnapshot } from "../../contracts/generated/ui";

describe("LayoutSerializer and Migration", () => {
  it("computes deterministic SHA-256 content hashes", async () => {
    const hash1 = await computeContentHash("sample-layout-json-content");
    const hash2 = await computeContentHash("sample-layout-json-content");
    expect(hash1).toBe(hash2);
    expect(hash1).toHaveLength(64);
  });

  it("diagnoses incompatible widgets during layout restoration", () => {
    const registry = new WidgetRegistry();
    registry.registerWidget({
      descriptor: {
        widget_type: "widget_A",
        owning_feature: "FEAT-UI-START_WORK",
        type_version: 1,
        schema_version: 1,
      },
      component: () => null,
    });

    const mockApi: any = {
      panels: [],
      clear: () => {},
      addPanel: () => {},
    };

    const snapshot: WorkspaceLayoutSnapshot = {
      layout_id: "layout-1",
      workspace_id: "ws-1",
      actor_id: "actor-1",
      layout_version: 1,
      capability_snapshot_id: "snap-1",
      widget_instances: [
        {
          instance_id: "inst-1",
          widget_type: "widget_A",
          workspace_id: "ws-1",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
        {
          instance_id: "inst-2",
          widget_type: "widget_B",
          workspace_id: "ws-1",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
      ],
      placements: [],
      content_hash: "hash-test",
      schema_version: 1,
    };

    const result = restoreLayout(mockApi, snapshot, registry);
    expect(result.migrated).toBe(true);
    expect(result.incompatible_widgets).toContain("widget_B");
    expect(result.incompatible_widgets).not.toContain("widget_A");
    expect(result.diagnostics?.length).toBeGreaterThan(0);
  });

  it("handles layout migration between versions", () => {
    const snapshot: WorkspaceLayoutSnapshot = {
      layout_id: "layout-1",
      workspace_id: "ws-1",
      actor_id: "actor-1",
      layout_version: 1,
      capability_snapshot_id: "snap-1",
      content_hash: "hash",
      schema_version: 1,
    };

    const result = migrateLayout(snapshot, 2);
    expect(result.source_layout_version).toBe(1);
    expect(result.target_layout_version).toBe(2);
    expect(result.migrated).toBe(true);
  });
});
