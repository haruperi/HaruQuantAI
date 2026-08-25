/**
 * WorkspaceHost Component for HaruQuantAI D-UI.
 *
 * Provides the interactive workstation canvas including the DockviewAdapter,
 * toolbar for adding widgets / applying templates, layout autosave/serialization,
 * and dirty-close resolution dialog.
 */

import React, { useState, useCallback } from "react";
import type { DockviewApi } from "dockview-react";
import type {
  WidgetTypeDescriptor,
  WorkspaceLayoutSnapshot,
} from "../contracts/generated/ui";
import { WidgetRegistry } from "../runtime/widget_registry";
import { DockviewAdapter } from "./DockviewAdapter";
import { WidgetCatalogue } from "./WidgetCatalogue";
import { TemplateManager } from "./template_manager";
import { restoreLayout, serializeLayout } from "./layout_serializer";

export interface WorkspaceHostProps {
  workspaceId: string;
  registry: WidgetRegistry;
  templateManager?: TemplateManager;
  initialLayout?: WorkspaceLayoutSnapshot | null;
  onLayoutPersisted?: (snapshot: WorkspaceLayoutSnapshot) => void;
  className?: string;
}

export const WorkspaceHost: React.FC<WorkspaceHostProps> = ({
  workspaceId,
  registry,
  templateManager = new TemplateManager(),
  initialLayout,
  onLayoutPersisted,
  className = "workspace-host-container",
}) => {
  const [api, setApi] = useState<DockviewApi | null>(null);
  const [isCatalogueOpen, setIsCatalogueOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("template-research-v1");
  const [dirtyPrompt] = useState<{
    instanceId: string;
    onConfirm: () => void;
    onCancel: () => void;
  } | null>(null);

  const handleDockviewReady = useCallback(
    (dockviewApi: DockviewApi) => {
      setApi(dockviewApi);

      if (initialLayout && initialLayout.widget_instances && initialLayout.widget_instances.length > 0) {
        restoreLayout(dockviewApi, initialLayout, registry);
      } else {
        // Instantiate default template
        const defaultSnapshot = templateManager.instantiateTemplate(
          selectedTemplate,
          workspaceId
        );
        restoreLayout(dockviewApi, defaultSnapshot, registry);
      }
    },
    [initialLayout, registry, selectedTemplate, templateManager, workspaceId]
  );

  const handleLayoutChange = useCallback(
    async (dockviewApi: DockviewApi) => {
      try {
        const snapshot = await serializeLayout(dockviewApi, workspaceId, "actor-current");
        onLayoutPersisted?.(snapshot);
      } catch (err) {
        console.error("Failed to serialize layout change:", err);
      }
    },
    [workspaceId, onLayoutPersisted]
  );

  const handleAddWidget = (descriptor: WidgetTypeDescriptor) => {
    if (!api) return;

    const instanceId = `inst-${descriptor.widget_type}-${Date.now()}`;
    api.addPanel({
      id: instanceId,
      component: "widgetPanel",
      title: descriptor.widget_type,
      params: {
        instance: {
          instance_id: instanceId,
          widget_type: descriptor.widget_type,
          workspace_id: workspaceId,
          configuration_version: 1,
          state_version: 1,
          schema_version: 1,
        },
        registry,
      },
    });

    setIsCatalogueOpen(false);
  };

  const handleApplyTemplate = (templateId: string) => {
    if (!api) return;
    setSelectedTemplate(templateId);
    const snapshot = templateManager.instantiateTemplate(templateId, workspaceId);
    restoreLayout(api, snapshot, registry);
  };

  const handleClearLayout = () => {
    if (!api) return;
    api.clear();
  };

  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        position: "relative",
      }}
      data-testid="workspace-host"
    >
      {/* Workstation Canvas Controls Toolbar */}
      <div
        className="workspace-toolbar"
        role="toolbar"
        aria-label="Workspace canvas controls"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "8px 12px",
          backgroundColor: "#0f172a",
          borderBottom: "1px solid #334155",
          color: "#f8fafc",
          fontSize: "13px",
        }}
      >
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            type="button"
            onClick={() => setIsCatalogueOpen(true)}
            style={{
              padding: "5px 12px",
              backgroundColor: "#0284c7",
              color: "#ffffff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            + Add Widget
          </button>

          <label htmlFor="template-select" style={{ color: "#94a3b8", marginLeft: "12px" }}>
            Template:
          </label>
          <select
            id="template-select"
            value={selectedTemplate}
            onChange={(e) => handleApplyTemplate(e.target.value)}
            style={{
              padding: "4px 8px",
              borderRadius: "4px",
              backgroundColor: "#1e293b",
              color: "#f8fafc",
              border: "1px solid #475569",
            }}
          >
            {templateManager.getTemplates().map((t) => (
              <option key={t.template_id} value={t.template_id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <button
            type="button"
            onClick={handleClearLayout}
            style={{
              padding: "4px 10px",
              backgroundColor: "#334155",
              color: "#cbd5e1",
              border: "1px solid #475569",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Clear Canvas
          </button>
        </div>
      </div>

      {/* Main Dockview Adapter Container */}
      <div style={{ flex: 1, position: "relative", minHeight: 0 }}>
        <DockviewAdapter
          registry={registry}
          layout={initialLayout}
          onReady={handleDockviewReady}
          onLayoutChange={handleLayoutChange}
        />
      </div>

      {/* Widget Catalogue Modal */}
      {isCatalogueOpen && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.6)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
          }}
        >
          <WidgetCatalogue
            registry={registry}
            onSelectWidget={handleAddWidget}
            onClose={() => setIsCatalogueOpen(false)}
          />
        </div>
      )}

      {/* Dirty Tab Close Confirmation Modal */}
      {dirtyPrompt && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.6)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1001,
          }}
          role="alertdialog"
          aria-labelledby="dirty-prompt-title"
        >
          <div
            style={{
              backgroundColor: "#1e293b",
              padding: "20px",
              borderRadius: "8px",
              maxWidth: "400px",
              color: "#f8fafc",
            }}
          >
            <h4 id="dirty-prompt-title" style={{ margin: "0 0 12px 0" }}>
              Unsaved Changes
            </h4>
            <p style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "16px" }}>
              This tab contains unsaved changes. Closing it will discard your draft.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button
                type="button"
                onClick={dirtyPrompt.onCancel}
                style={{
                  padding: "6px 12px",
                  backgroundColor: "#334155",
                  color: "#f8fafc",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={dirtyPrompt.onConfirm}
                style={{
                  padding: "6px 12px",
                  backgroundColor: "#e11d48",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Discard & Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
