'use client';

/**
 * Docking layout host (FEAT-UI-01/16, FR-UI-006/007/008/024/200/202).
 *
 * Hosts a Dockview docking layout for one workspace, mirroring the CME Group
 * Simulator's workspace behaviour: fluid pixel-level splitters between regions,
 * tab dragging that docks into groups or splits regions at edges, automatic
 * refill of vacated regions, per-group maximize (double-click a tab), and
 * Alt+Arrow keyboard panel moves. The store's widget list is the panel
 * registry; the serialized layout tree persists through the store and is
 * rebuilt deterministically for legacy grid layouts and template presets
 * (FR-UI-201).
 */
import React, { useCallback, useEffect, useRef } from 'react';
import {
  DockviewReact,
  DockviewDefaultTab,
  type DockviewApi,
  type DockviewReadyEvent,
  type IDockviewPanelHeaderProps,
  type IDockviewPanelProps,
  type SerializedDockview,
} from 'dockview-react';
import 'dockview-core/dist/styles/dockview.css';

import {
  useWorkspaceStore,
  buildDockLayout,
  DOCK_WIDGET_COMPONENT,
  type Widget,
  type Workspace,
  type WorkspaceStoreState,
} from '../../features/workspaces';
import { WidgetContentHost } from './WidgetContentHost';

/** Stable selector for one widget of the active workspace (registry lookup). */
const selectDockWidget =
  (widgetId: string) =>
  (state: WorkspaceStoreState): Widget | undefined => {
    const ws = state.workspaces.find((w) => String(w.id) === String(state.activeWorkspaceId));
    return ws?.widgets.find((w) => w.id === widgetId);
  };

/** Panel content: renders the registered widget through the shared host. */
const DockWidgetPanel: React.FC<IDockviewPanelProps> = ({ params }) => {
  const widgetId = String(params?.widgetId ?? '');
  const widget = useWorkspaceStore(selectDockWidget(widgetId));
  if (!widget) return null;
  return <WidgetContentHost widget={widget} />;
};

/** Default tab plus double-click to maximize/restore the group (FR-UI-008). */
const DockWidgetTab: React.FC<IDockviewPanelHeaderProps> = (props) => {
  const toggleExpandWidget = useWorkspaceStore((state) => state.toggleExpandWidget);
  return (
    <div
      className="workspace-dock-tab"
      title="Double-click to expand this group to fill the workspace"
      onDoubleClick={() => toggleExpandWidget(props.api.id)}
    >
      <DockviewDefaultTab {...props} />
    </div>
  );
};

export const DockingWorkspace: React.FC<{ workspace: Workspace }> = ({ workspace }) => {
  const apiRef = useRef<DockviewApi | null>(null);
  const workspaceRef = useRef(workspace);
  workspaceRef.current = workspace;

  const setWorkspaceDockLayout = useWorkspaceStore((state) => state.setWorkspaceDockLayout);
  const removeWidget = useWorkspaceStore((state) => state.removeWidget);

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Suppress saves while a persisted/factory layout is being loaded, so the
  // restore's own layout-change events cannot feed back into the store.
  const suppressSave = useRef(false);

  const scheduleSave = useCallback(() => {
    if (suppressSave.current) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const api = apiRef.current;
      const ws = workspaceRef.current;
      if (!api || !ws) return;
      try {
        setWorkspaceDockLayout(ws.id, api.toJSON());
      } catch {
        // A failed serialization must never break the live workspace.
      }
    }, 250);
  }, [setWorkspaceDockLayout]);

  const onReady = useCallback(
    (event: DockviewReadyEvent) => {
      const api = event.api;
      apiRef.current = api;

      const ws = workspaceRef.current;
      suppressSave.current = true;

      let restored = false;
      if (ws.dock) {
        try {
          api.fromJSON(ws.dock as SerializedDockview);
          restored = api.panels.length > 0;
        } catch {
          restored = false;
        }
      }
      if (!restored) {
        // Legacy grid layouts and fresh template presets both arrive as
        // widget rectangles; convert them deterministically (FR-UI-201).
        const layout = buildDockLayout(ws.widgets);
        if (layout) {
          try {
            api.fromJSON(layout);
            restored = api.panels.length > 0;
          } catch {
            restored = false;
          }
        }
      }
      if (!restored) {
        // Last-resort sequential fallback: one panel per widget.
        for (const widget of ws.widgets) {
          api.addPanel({
            id: widget.id,
            title: widget.title,
            component: DOCK_WIDGET_COMPONENT,
            params: { widgetId: widget.id },
          });
        }
      }

      api.onDidRemovePanel((panel) => {
        // A panel closed through the dock UI (tab close) syncs back to the registry.
        removeWidget(panel.id);
      });
      api.onDidLayoutChange(() => scheduleSave());
      setTimeout(() => {
        suppressSave.current = false;
      }, 0);
    },
    [removeWidget, scheduleSave]
  );

  // Registry <-> panel reconciliation: new widgets become panels (docked as a
  // tab in the active group when one exists), removed widgets' panels close,
  // and tab titles follow the registry.
  useEffect(() => {
    const api = apiRef.current;
    if (!api) return undefined;
    const panelIds = new Set(api.panels.map((panel) => panel.id));

    for (const widget of workspace.widgets) {
      if (!panelIds.has(widget.id)) {
        const activeId = api.activePanel?.id;
        api.addPanel(
          activeId
            ? {
                id: widget.id,
                title: widget.title,
                component: DOCK_WIDGET_COMPONENT,
                params: { widgetId: widget.id },
                position: { referencePanel: activeId, direction: 'within' },
              }
            : {
                id: widget.id,
                title: widget.title,
                component: DOCK_WIDGET_COMPONENT,
                params: { widgetId: widget.id },
              }
        );
      } else {
        const panel = api.getPanel(widget.id);
        if (panel && panel.title !== widget.title) {
          panel.api.setTitle(widget.title);
        }
      }
    }
    for (const id of panelIds) {
      if (!workspace.widgets.some((widget) => widget.id === id)) {
        api.getPanel(id)?.api.close();
      }
    }
    return undefined;
  }, [workspace.widgets]);

  // Expanded mode maps to group maximize (FR-UI-008): the maximized group
  // fills the workspace and every other region is restored on contract.
  useEffect(() => {
    const api = apiRef.current;
    if (!api) return undefined;
    if (workspace.expandedWidgetId) {
      const panel = api.getPanel(workspace.expandedWidgetId);
      if (panel && !panel.api.isMaximized()) panel.api.maximize();
    } else {
      for (const panel of api.panels) {
        if (panel.api.isMaximized()) panel.api.exitMaximized();
      }
    }
    return undefined;
  }, [workspace.expandedWidgetId]);

  // Keyboard layout moves (FR-UI-007): Alt+Arrow on the focused layout moves
  // the active panel left/right/above/below its group, docking or splitting
  // exactly like a tab drag to that edge.
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const api = apiRef.current;
    const panel = api?.activePanel;
    if (!panel) return;
    const position =
      event.key === 'ArrowLeft'
        ? 'left'
        : event.key === 'ArrowRight'
          ? 'right'
          : event.key === 'ArrowUp'
            ? 'top'
            : event.key === 'ArrowDown'
              ? 'bottom'
              : null;
    if (!position) return;
    event.preventDefault();
    panel.api.moveTo({ group: panel.api.group, position });
  };

  useEffect(
    () => () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    },
    []
  );

  return (
    <div className="workspace-dock-shell dockview-theme-dark" onKeyDown={handleKeyDown}>
      <DockviewReact
        className="workspace-dockview"
        onReady={onReady}
        components={{ [DOCK_WIDGET_COMPONENT]: DockWidgetPanel }}
        defaultTabComponent={DockWidgetTab}
      />
    </div>
  );
};
