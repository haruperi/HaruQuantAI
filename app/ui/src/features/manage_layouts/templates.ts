/**
 * Versioned workspace templates for FEAT-UI-MANAGE_LAYOUTS.
 *
 * The six presets are harvested from the V2 donor
 * (`.migration/v2-ui/src/widgets/workspaces/templates.ts`, provenance
 * UI_MIGRATION_PLAN.md §6 row 1.3) and converted V3-natively into
 * `WorkspaceTemplate` snapshots. Conversion uses an adapted guillotine
 * partition of the donor's nominal grid rectangles (algorithm derived from
 * the donor's `dockLayout.ts`): column clusters become side-by-side panels
 * sized by width share; widgets in the same cluster become tabs ordered by
 * row. No donor module is imported.
 *
 * Widget type names follow the donor's domain slugs (snake_case). Until the
 * corresponding V3 features register those widget types, restoration
 * diagnoses them as missing via the engine's INCOMPATIBLE_WIDGET path and
 * falls back to deterministic defaults — the same convention the engine's
 * builtin templates already use (see `workspaces/template_manager.ts`).
 */

import type {
  WorkspaceLayoutSnapshot,
  WorkspaceTemplate,
  WidgetInstanceRef,
  WidgetPlacement,
} from "../../contracts/generated/ui";
import { TemplateManager } from "../../workspaces/template_manager";

/** Minimal donor preset shape used for conversion (V3-local). */
interface DonorPreset {
  readonly type: string;
  readonly title: string;
  readonly col: number;
  readonly row: number;
  readonly colSpan: number;
  readonly rowSpan: number;
}

/** Donor template seed (harvested data, not imported code). */
interface DonorTemplateSeed {
  readonly id: string;
  readonly name: string;
  readonly widgets: readonly DonorPreset[];
}

const DONOR_TEMPLATE_SEEDS: readonly DonorTemplateSeed[] = [
  {
    id: "haruquant",
    name: "HaruQuant",
    widgets: [
      { type: "markets", title: "Markets", col: 1, row: 1, colSpan: 4, rowSpan: 8 },
      { type: "trade_plan", title: "Calendar", col: 1, row: 9, colSpan: 4, rowSpan: 9 },
      { type: "chart", title: "EURUSD Chart", col: 5, row: 1, colSpan: 4, rowSpan: 17 },
      { type: "positions", title: "Positions", col: 1, row: 18, colSpan: 4, rowSpan: 9 },
      { type: "trade_log", title: "Orders", col: 5, row: 18, colSpan: 4, rowSpan: 9 },
      { type: "price_ladder", title: "EURUSD DOM", col: 9, row: 1, colSpan: 4, rowSpan: 26 },
    ],
  },
  {
    id: "chart-ladder",
    name: "Chart + Ladder",
    widgets: [
      { type: "markets", title: "Markets", col: 1, row: 1, colSpan: 3, rowSpan: 12 },
      { type: "trade_plan", title: "Calendar", col: 1, row: 13, colSpan: 3, rowSpan: 13 },
      { type: "chart", title: "EURUSD Chart", col: 4, row: 1, colSpan: 6, rowSpan: 25 },
      { type: "price_ladder", title: "EURUSD DOM", col: 10, row: 1, colSpan: 3, rowSpan: 25 },
    ],
  },
  {
    id: "multicharts-ladder",
    name: "MultiCharts + Ladder",
    widgets: [
      { type: "chart", title: "EURUSD Chart", col: 1, row: 1, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "GBPUSD Chart", col: 6, row: 1, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "USDJPY Chart", col: 11, row: 1, colSpan: 5, rowSpan: 2 },
      { type: "trade_plan", title: "Calendar", col: 16, row: 1, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "XAUUSD Chart", col: 1, row: 3, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "AUDUSD Chart", col: 6, row: 3, colSpan: 5, rowSpan: 2 },
      { type: "chart", title: "USDCHF Chart", col: 11, row: 3, colSpan: 5, rowSpan: 2 },
      { type: "positions", title: "Positions & Orders", col: 16, row: 3, colSpan: 5, rowSpan: 2 },
      { type: "price_ladder", title: "EURUSD DOM", col: 1, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "price_ladder", title: "GBPUSD DOM", col: 5, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "price_ladder", title: "USDJPY DOM", col: 9, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "price_ladder", title: "XAUUSD DOM", col: 13, row: 5, colSpan: 4, rowSpan: 4 },
      { type: "price_ladder", title: "AUDUSD DOM", col: 17, row: 5, colSpan: 4, rowSpan: 4 },
    ],
  },
  {
    id: "options",
    name: "Options",
    widgets: [
      { type: "markets", title: "Markets", col: 1, row: 1, colSpan: 6, rowSpan: 14 },
      { type: "options_grid", title: "EURUSD Options", col: 7, row: 1, colSpan: 6, rowSpan: 23 },
      { type: "positions", title: "Positions & Orders", col: 1, row: 15, colSpan: 6, rowSpan: 9 },
    ],
  },
  {
    id: "charts",
    name: "Charts",
    widgets: [
      { type: "chart", title: "EURUSD Chart", col: 1, row: 1, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "GBPUSD Chart", col: 4, row: 1, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "USDJPY Chart", col: 7, row: 1, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "XAUUSD Chart", col: 10, row: 1, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "AUDUSD Chart", col: 1, row: 2, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "USDCHF Chart", col: 4, row: 2, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "USDCAD Chart", col: 7, row: 2, colSpan: 3, rowSpan: 1 },
      { type: "chart", title: "NZDUSD Chart", col: 10, row: 2, colSpan: 3, rowSpan: 1 },
    ],
  },
];

interface ColumnCluster {
  readonly start: number;
  readonly end: number;
  readonly presets: readonly DonorPreset[];
}

function clusterByColumns(presets: readonly DonorPreset[]): ColumnCluster[] {
  const sorted = [...presets].sort((a, b) => a.col - b.col || a.row - b.row);
  const clusters: {
    start: number;
    end: number;
    presets: DonorPreset[];
  }[] = [];
  for (const preset of sorted) {
    const start = preset.col;
    const end = preset.col + preset.colSpan - 1;
    const overlapping = clusters.find((c) => start <= c.end && end >= c.start);
    if (overlapping) {
      overlapping.start = Math.min(overlapping.start, start);
      overlapping.end = Math.max(overlapping.end, end);
      overlapping.presets.push(preset);
    } else {
      clusters.push({ start, end, presets: [preset] });
    }
  }
  return clusters;
}

function totalClusterWidth(clusters: readonly ColumnCluster[]): number {
  const min = Math.min(...clusters.map((c) => c.start));
  const max = Math.max(...clusters.map((c) => c.end));
  return max - min + 1;
}

export function buildLayoutSnapshotFromSeed(
  seed: DonorTemplateSeed
): WorkspaceLayoutSnapshot {
  const clusters = clusterByColumns(seed.widgets);
  const totalWidth = totalClusterWidth(clusters);

  const widgetInstances: WidgetInstanceRef[] = [];
  const placements: WidgetPlacement[] = [];

  clusters.forEach((cluster, panelIndex) => {
    const ordered = [...cluster.presets].sort((a, b) => a.row - b.row);
    ordered.forEach((preset, tabIndex) => {
      const instanceId = `inst-tpl-${seed.id}-${preset.type}-${tabIndex}`;
      widgetInstances.push({
        instance_id: instanceId,
        widget_type: preset.type,
        workspace_id: `template-${seed.id}`,
        configuration_version: 1,
        state_version: 1,
        schema_version: 1,
      });
      placements.push({
        instance_id: instanceId,
        panel_id: `panel-tpl-${seed.id}-${panelIndex}`,
        panel_order: panelIndex,
        tab_order: tabIndex,
        size_ratio: `${(cluster.end - cluster.start + 1) / totalWidth}`,
        schema_version: 1,
      });
    });
  });

  return {
    layout_id: `layout-template-${seed.id}`,
    workspace_id: `template-${seed.id}`,
    actor_id: "system",
    layout_version: 1,
    capability_snapshot_id: `snap-template-${seed.id}`,
    widget_instances: widgetInstances,
    placements,
    active_panel_id: widgetInstances[0]?.instance_id ?? null,
    content_hash: `template-${seed.id}-hash`,
    schema_version: 1,
  };
}

export const MANAGE_LAYOUTS_TEMPLATES: readonly WorkspaceTemplate[] =
  DONOR_TEMPLATE_SEEDS.map((seed) => ({
    template_id: `template-${seed.id}-v1`,
    name: seed.name,
    description: `Harvested V2 preset "${seed.id}" converted to a versioned workspace template (mock-stage widget slugs).`,
    layout: buildLayoutSnapshotFromSeed(seed),
    schema_version: 1,
  }));

export function buildTemplateManager(): TemplateManager {
  const manager = new TemplateManager();
  for (const template of MANAGE_LAYOUTS_TEMPLATES) {
    manager.registerTemplate(template);
  }
  return manager;
}

export function findManageLayoutsTemplate(
  templateId: string
): WorkspaceTemplate | undefined {
  return MANAGE_LAYOUTS_TEMPLATES.find((t) => t.template_id === templateId);
}
