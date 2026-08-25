/**
 * WorkspaceHost Component for HaruQuantAI D-UI.
 *
 * Provides the interactive workstation canvas including the DockviewAdapter,
 * toolbar for adding widgets / applying templates, layout autosave/serialization,
 * and dirty-close resolution dialog.
 */

import React, { useState, useCallback, useRef, useEffect } from "react";
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

/** Minimal persistence surface consumed by WorkspaceHost (FR-UI-PERSIST_LAYOUTS). */
export interface LayoutPersistenceLike {
  save(workspaceId: string, snapshot: WorkspaceLayoutSnapshot): void;
  load(workspaceId: string): {
    snapshot: WorkspaceLayoutSnapshot | null;
    diagnostics: readonly { code: string; detail: string }[];
  };
}

/** Subscription surface for external template requests (workspace_templates widget). */
export interface TemplateRequestSubscriptionLike {
  subscribe(listener: (templateId: string) => void): () => void;
}

export interface WorkspaceHostProps {
  workspaceId: string;
  registry: WidgetRegistry;
  templateManager?: TemplateManager;
  initialLayout?: WorkspaceLayoutSnapshot | null;
  onLayoutPersisted?: (snapshot: WorkspaceLayoutSnapshot) => void;
  layoutPersistence?: LayoutPersistenceLike;
  templateRequests?: TemplateRequestSubscriptionLike;
  className?: string;
}

export const WorkspaceHost: React.FC<WorkspaceHostProps> = ({
  workspaceId,
  registry,
  templateManager = new TemplateManager(),
  initialLayout,
  onLayoutPersisted,
  layoutPersistence,
  templateRequests,
  className = "workspace-host-container",
}) => {
  const [api, setApi] = useState<DockviewApi | null>(null);
  const [isCatalogueOpen, setIsCatalogueOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("template-research-v1");
  const [dirtyPrompt, setDirtyPrompt] = useState<{
    instanceId: string;
    onConfirm: () => void;
    onCancel: () => void;
  } | null>(null);
  const dirtyPanelsRef = useRef<Set<string>>(new Set());
  const forceCloseRef = useRef<Set<string>>(new Set());

  const handleDockviewReady = useCallback(
    (dockviewApi: DockviewApi) => {
      setApi(dockviewApi);

      // FR-UI-MANAGE_TABS: veto closing dirty panels until explicit resolution.
      dockviewApi.onDidAddPanel((panel) => {
        const originalClose = panel.api.close.bind(panel.api);
        panel.api.close = () => {
          if (
            dirtyPanelsRef.current.has(panel.id) &&
            !forceCloseRef.current.has(panel.id)
          ) {
            setDirtyPrompt({
              instanceId: panel.id,
              onConfirm: () => {
                forceCloseRef.current.add(panel.id);
                originalClose();
                dirtyPanelsRef.current.delete(panel.id);
                forceCloseRef.current.delete(panel.id);
                setDirtyPrompt(null);
              },
              onCancel: () => setDirtyPrompt(null),
            });
            return;
          }
          originalClose();
        };
      });

      let restoreSource: WorkspaceLayoutSnapshot | null = initialLayout ?? null;
      if (
        !restoreSource ||
        (restoreSource.widget_instances?.length ?? 0) === 0
      ) {
        const persisted = layoutPersistence?.load(workspaceId);
        if (persisted?.snapshot) {
          restoreSource = persisted.snapshot;
        }
      }
      if (
        restoreSource &&
        restoreSource.widget_instances &&
        restoreSource.widget_instances.length > 0
      ) {
        restoreLayout(dockviewApi, restoreSource, registry);
      } else {
        // Instantiate default template
        const defaultSnapshot = templateManager.instantiateTemplate(
          selectedTemplate,
          workspaceId
        );
        restoreLayout(dockviewApi, defaultSnapshot, registry);
      }
    },
    [initialLayout, registry, selectedTemplate, templateManager, workspaceId, layoutPersistence]
  );

  // External template requests (workspace_templates widget) apply through
  // the same engine path as the toolbar select.
  useEffect(() => {
    if (!templateRequests || !api) return;
    return templateRequests.subscribe((templateId) => {
      handleApplyTemplate(templateId);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateRequests, api]);

  const handleLayoutChange = useCallback(
    async (dockviewApi: DockviewApi) => {
      try {
        const snapshot = await serializeLayout(dockviewApi, workspaceId, "actor-current");
        onLayoutPersisted?.(snapshot);
        if (layoutPersistence) {
          layoutPersistence.save(workspaceId, snapshot);
          dirtyPanelsRef.current.clear();
        }
      } catch (err) {
        console.error("Failed to serialize layout change:", err);
      }
    },
    [workspaceId, onLayoutPersisted, layoutPersistence]
  );

  const handleDirtyChange = useCallback((panelId: string, isDirty: boolean) => {
    if (isDirty) {
      dirtyPanelsRef.current.add(panelId);
    } else {
      dirtyPanelsRef.current.delete(panelId);
    }
  }, []);

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
        onDirtyChange: handleDirtyChange,
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
