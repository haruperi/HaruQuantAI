/**
 * Workspace Template Manager for HaruQuantAI D-UI.
 *
 * Provides versioned templates (Blank, Research, Data, Trading) and layout instantiation.
 */

import type { WorkspaceLayoutSnapshot, WorkspaceTemplate } from "../contracts/generated/ui";

export function createBlankLayout(
  workspaceId: string,
  actorId: string = "actor-default"
): WorkspaceLayoutSnapshot {
  return {
    layout_id: `layout-blank-${Date.now()}`,
    workspace_id: workspaceId,
    actor_id: actorId,
    layout_version: 1,
    capability_snapshot_id: "snap-default",
    widget_instances: [],
    placements: [],
    active_panel_id: null,
    content_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", // pragma: allowlist secret
    schema_version: 1,
  };
}

export const BUILTIN_TEMPLATES: readonly WorkspaceTemplate[] = [
  {
    template_id: "template-blank-v1",
    name: "Blank Workspace",
    description: "An empty workstation canvas ready for custom widget additions.",
    layout: createBlankLayout("template-blank"),
    schema_version: 1,
  },
  {
    template_id: "template-research-v1",
    name: "Research Workspace",
    description: "Pre-configured workspace with Research Builder, Monitor, and Result exploration widgets.",
    layout: {
      layout_id: "layout-preset-research",
      workspace_id: "preset-research",
      actor_id: "system",
      layout_version: 1,
      capability_snapshot_id: "snap-research",
      widget_instances: [
        {
          instance_id: "inst-research-builder",
          widget_type: "research_builder",
          workspace_id: "preset-research",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
        {
          instance_id: "inst-research-monitor",
          widget_type: "research_monitor",
          workspace_id: "preset-research",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
        {
          instance_id: "inst-result-overview",
          widget_type: "result_overview",
          workspace_id: "preset-research",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
      ],
      placements: [
        {
          instance_id: "inst-research-builder",
          panel_id: "panel-left",
          panel_order: 0,
          tab_order: 0,
          size_ratio: "0.5",
          schema_version: 1,
        },
        {
          instance_id: "inst-research-monitor",
          panel_id: "panel-right",
          panel_order: 1,
          tab_order: 0,
          size_ratio: "0.5",
          schema_version: 1,
        },
        {
          instance_id: "inst-result-overview",
          panel_id: "panel-right",
          panel_order: 1,
          tab_order: 1,
          size_ratio: "0.5",
          schema_version: 1,
        },
      ],
      active_panel_id: "inst-research-builder",
      content_hash: "preset-research-hash",
      schema_version: 1,
    },
    schema_version: 1,
  },
  {
    template_id: "template-data-v1",
    name: "Data Workspace",
    description: "Dataset management, instruments, and trading session configuration.",
    layout: {
      layout_id: "layout-preset-data",
      workspace_id: "preset-data",
      actor_id: "system",
      layout_version: 1,
      capability_snapshot_id: "snap-data",
      widget_instances: [
        {
          instance_id: "inst-datasets",
          widget_type: "datasets",
          workspace_id: "preset-data",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
        {
          instance_id: "inst-instruments",
          widget_type: "instruments",
          workspace_id: "preset-data",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
      ],
      placements: [
        {
          instance_id: "inst-datasets",
          panel_id: "panel-data-left",
          panel_order: 0,
          tab_order: 0,
          size_ratio: "0.5",
          schema_version: 1,
        },
        {
          instance_id: "inst-instruments",
          panel_id: "panel-data-right",
          panel_order: 1,
          tab_order: 0,
          size_ratio: "0.5",
          schema_version: 1,
        },
      ],
      active_panel_id: "inst-datasets",
      content_hash: "preset-data-hash",
      schema_version: 1,
    },
    schema_version: 1,
  },
  {
    template_id: "template-trading-v1",
    name: "Trading Workspace",
    description: "Operational trading view with session controls, order ticket, and positions/orders monitoring.",
    layout: {
      layout_id: "layout-preset-trading",
      workspace_id: "preset-trading",
      actor_id: "system",
      layout_version: 1,
      capability_snapshot_id: "snap-trading",
      widget_instances: [
        {
          instance_id: "inst-order-ticket",
          widget_type: "order_ticket",
          workspace_id: "preset-trading",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
        {
          instance_id: "inst-positions-orders",
          widget_type: "positions_orders",
          workspace_id: "preset-trading",
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
      ],
      placements: [
        {
          instance_id: "inst-order-ticket",
          panel_id: "panel-trading-top",
          panel_order: 0,
          tab_order: 0,
          size_ratio: "0.5",
          schema_version: 1,
        },
        {
          instance_id: "inst-positions-orders",
          panel_id: "panel-trading-bottom",
          panel_order: 1,
          tab_order: 0,
          size_ratio: "0.5",
          schema_version: 1,
        },
      ],
      active_panel_id: "inst-order-ticket",
      content_hash: "preset-trading-hash",
      schema_version: 1,
    },
    schema_version: 1,
  },
];

export class TemplateManager {
  private readonly templates = new Map<string, WorkspaceTemplate>();

  constructor(customTemplates: readonly WorkspaceTemplate[] = []) {
    for (const t of BUILTIN_TEMPLATES) {
      this.templates.set(t.template_id, t);
    }
    for (const t of customTemplates) {
      this.templates.set(t.template_id, t);
    }
  }

  public getTemplates(): WorkspaceTemplate[] {
    return Array.from(this.templates.values());
  }

  public getTemplate(templateId: string): WorkspaceTemplate | undefined {
    return this.templates.get(templateId);
  }

  public registerTemplate(template: WorkspaceTemplate): void {
    this.templates.set(template.template_id, template);
  }

  public instantiateTemplate(
    templateId: string,
    targetWorkspaceId: string,
    actorId: string = "actor-default"
  ): WorkspaceLayoutSnapshot {
    const template = this.templates.get(templateId);
    if (!template) {
      return createBlankLayout(targetWorkspaceId, actorId);
    }

    const layout = template.layout;
    const instanceMap = new Map<string, string>();

    const widgetInstances = (layout.widget_instances || []).map((inst, index) => {
      const newInstanceId = `inst-${inst.widget_type}-${Date.now()}-${index}`;
      instanceMap.set(inst.instance_id, newInstanceId);
      return {
        ...inst,
        instance_id: newInstanceId,
        workspace_id: targetWorkspaceId,
      };
    });

    const placements = (layout.placements || []).map((p) => ({
      ...p,
      instance_id: instanceMap.get(p.instance_id) || p.instance_id,
    }));

    return {
      ...layout,
      layout_id: `layout-${targetWorkspaceId}-${Date.now()}`,
      workspace_id: targetWorkspaceId,
      actor_id: actorId,
      widget_instances: widgetInstances,
      placements,
    };
  }
}
