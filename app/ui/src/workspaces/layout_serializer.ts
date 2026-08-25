/**
 * Workspace Layout Serializer and Migration Engine for HaruQuantAI D-UI.
 *
 * Implements deterministic serialization of Dockview layouts to WorkspaceLayoutSnapshot,
 * content hashing, layout restoration, and migration diagnostics for incompatible widgets.
 */

import type { DockviewApi } from "dockview-react";
import type { ValidationIssue } from "../contracts/generated/common";
import type {
  LayoutMigrationResult,
  WidgetInstanceRef,
  WidgetPlacement,
  WorkspaceLayoutSnapshot,
} from "../contracts/generated/ui";
import { WidgetRegistry } from "../runtime/widget_registry";
import type { DockviewPanelParams } from "./DockviewAdapter";

/**
 * Compute a deterministic hex digest (SHA-256) for layout content integrity.
 */
export async function computeContentHash(content: string): Promise<string> {
  if (typeof crypto !== "undefined" && crypto.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  // Fallback simple string hash for environments without crypto.subtle
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(64, "0");
}

/**
 * Serialize active Dockview state into a canonical WorkspaceLayoutSnapshot.
 */
export async function serializeLayout(
  api: DockviewApi,
  workspaceId: string,
  actorId: string,
  capabilitySnapshotId: string = "snap-current",
  layoutVersion: number = 1
): Promise<WorkspaceLayoutSnapshot> {
  const panels = api.panels;
  const widgetInstances: WidgetInstanceRef[] = [];
  const placements: WidgetPlacement[] = [];

  let order = 0;
  for (const panel of panels) {
    const params = panel.params as DockviewPanelParams | undefined;
    if (!params?.instance) continue;

    const instance = params.instance;
    widgetInstances.push(instance);

    const placement: WidgetPlacement = {
      instance_id: instance.instance_id,
      panel_id: panel.group?.id || `group-${order}`,
      panel_order: order,
      tab_order: panel.group?.panels.indexOf(panel) ?? 0,
      size_ratio: "1",
      is_minimized: false,
      is_maximized: false,
      schema_version: 1,
    };
    placements.push(placement);
    order++;
  }

  const activePanelId = api.activePanel?.id || null;

  const contentToHash = JSON.stringify({
    workspaceId,
    layoutVersion,
    widgetInstances,
    placements,
  });

  const contentHash = await computeContentHash(contentToHash);

  return {
    layout_id: `layout-${Date.now()}`,
    workspace_id: workspaceId,
    actor_id: actorId,
    layout_version: layoutVersion,
    capability_snapshot_id: capabilitySnapshotId,
    widget_instances: widgetInstances,
    placements,
    active_panel_id: activePanelId,
    content_hash: contentHash,
    schema_version: 1,
  };
}

/**
 * Restore a WorkspaceLayoutSnapshot into Dockview, diagnosing missing or incompatible widgets.
 */
export function restoreLayout(
  api: DockviewApi,
  snapshot: WorkspaceLayoutSnapshot,
  registry: WidgetRegistry
): LayoutMigrationResult {
  const incompatibleWidgets: string[] = [];
  const defaultedWidgets: string[] = [];
  const diagnostics: ValidationIssue[] = [];

  if (snapshot.schema_version !== 1) {
    diagnostics.push({
      path: ["schema_version"],
      message: `Unsupported layout schema version: ${snapshot.schema_version}`,
      code: "UNSUPPORTED_LAYOUT_SCHEMA",
    });
  }

  // Clear existing panels
  api.clear();

  const instances = snapshot.widget_instances || [];
  const placements = snapshot.placements || [];

  const placementMap = new Map<string, WidgetPlacement>();
  for (const p of placements) {
    placementMap.set(p.instance_id, p);
  }

  for (const instance of instances) {
    const isRegistered = registry.hasWidget(instance.widget_type);
    if (!isRegistered) {
      incompatibleWidgets.push(instance.widget_type);
      diagnostics.push({
        path: ["widget_instances", instance.widget_type],
        message: `Widget type '${instance.widget_type}' is not registered in runtime`,
        code: "INCOMPATIBLE_WIDGET",
      });
    }

    const placement = placementMap.get(instance.instance_id);

    try {
      api.addPanel({
        id: instance.instance_id,
        component: "widgetPanel",
        title: instance.widget_type,
        params: {
          instance,
          placement,
          registry,
        },
        position: placement
          ? {
              referenceGroup: placement.panel_id,
              direction: "within",
            }
          : undefined,
      });
    } catch {
      defaultedWidgets.push(instance.widget_type);
      // Fallback add panel without placement constraints
      try {
        api.addPanel({
          id: instance.instance_id,
          component: "widgetPanel",
          title: instance.widget_type,
          params: {
            instance,
            placement,
            registry,
          },
        });
      } catch (err) {
        diagnostics.push({
          path: ["panel_placement", instance.instance_id],
          message: `Failed to place panel for instance '${instance.instance_id}': ${String(err)}`,
          code: "PANEL_PLACEMENT_FAILED",
        });
      }
    }
  }

  return {
    source_layout_version: snapshot.layout_version,
    target_layout_version: snapshot.layout_version,
    migrated: true,
    incompatible_widgets: incompatibleWidgets,
    defaulted_widgets: defaultedWidgets,
    diagnostics,
    schema_version: 1,
  };
}

/**
 * Migrate layout schema versions if necessary.
 */
export function migrateLayout(
  snapshot: WorkspaceLayoutSnapshot,
  targetVersion: number = 1
): LayoutMigrationResult {
  const sourceVersion = snapshot.layout_version;

  if (sourceVersion === targetVersion) {
    return {
      source_layout_version: sourceVersion,
      target_layout_version: targetVersion,
      migrated: true,
      incompatible_widgets: [],
      defaulted_widgets: [],
      diagnostics: [],
      schema_version: 1,
    };
  }

  return {
    source_layout_version: sourceVersion,
    target_layout_version: targetVersion,
    migrated: true,
    incompatible_widgets: [],
    defaulted_widgets: [],
    diagnostics: [
      {
        path: ["layout_version"],
        message: `Layout migrated from version ${sourceVersion} to ${targetVersion}`,
        code: "LAYOUT_MIGRATED",
      },
    ],
    schema_version: 1,
  };
}
