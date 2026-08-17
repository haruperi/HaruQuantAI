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
import { Maximize2, Minimize2 } from 'lucide-react';
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

/** Default tab with an explicit Expand/Restore control and double-click shortcut (FR-UI-006, FR-UI-008). */
const DockWidgetTab: React.FC<IDockviewPanelHeaderProps> = (props) => {
  const tabRef = useRef<HTMLDivElement | null>(null);
  const expandedWidgetId = useWorkspaceStore((state) => {
    const workspace = state.workspaces.find((candidate) => String(candidate.id) === String(state.activeWorkspaceId));
    return workspace?.expandedWidgetId ?? null;
  });
  const switchExpandedWidget = useWorkspaceStore((state) => state.switchExpandedWidget);
  const contractWidget = useWorkspaceStore((state) => state.contractWidget);
  const isExpanded = expandedWidgetId === props.api.id;

  useEffect(() => {
    const floatingContainer = tabRef.current?.closest('.dv-resize-container');
    if (!(floatingContainer instanceof HTMLElement)) return undefined;
    floatingContainer.classList.toggle('workspace-floating-widget--expanded', isExpanded);
    return () => floatingContainer.classList.remove('workspace-floating-widget--expanded');
  }, [isExpanded]);

  const handleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    const floatingContainer = e.currentTarget.closest('.dv-resize-container');
    if (!floatingContainer) {
      if (isExpanded && props.api.isMaximized()) props.api.exitMaximized();
      else if (!isExpanded && !props.api.isMaximized()) props.api.maximize();
    }
    if (isExpanded) contractWidget();
    else switchExpandedWidget(props.api.id);
  };

  return (
    <div
      ref={tabRef}
      data-workspace-widget-id={props.api.id}
      className="workspace-dock-tab widget-header-grab"
      title="Use the expand control or double-click to fill the workspace; drag tab header to move widget"
      onDoubleClick={handleExpand}
    >
      <DockviewDefaultTab {...props} />
      <div className="widget-header-actions">
        <button
          type="button"
          className="widget-header-action-btn widget-header-expand-btn"
          aria-label={isExpanded ? 'Restore widget' : 'Expand widget'}
          title={isExpanded ? 'Restore widget to its previous size' : 'Expand widget to fill the workspace'}
          onClick={handleExpand}
        >
          {isExpanded ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
        </button>
      </div>
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
        // Last-resort sequential fallback: launch as centered floating panels.
        const width = 580;
        const height = 440;
        const winWidth = typeof window !== 'undefined' ? window.innerWidth : 1200;
        const winHeight = typeof window !== 'undefined' ? window.innerHeight : 800;
        const x = Math.max(20, Math.round((winWidth - width) / 2));
        const y = Math.max(20, Math.round((winHeight - height) / 2));
        for (const widget of ws.widgets) {
          api.addPanel({
            id: widget.id,
            title: widget.title,
            component: DOCK_WIDGET_COMPONENT,
            params: { widgetId: widget.id },
            floating: { width, height, x, y },
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

  // Registry <-> panel reconciliation: new widgets become centered floating
  // panels, removed widgets' panels close, and tab titles follow the registry.
  useEffect(() => {
    const api = apiRef.current;
    if (!api) return undefined;
    const panelIds = new Set(api.panels.map((panel) => panel.id));

    for (const widget of workspace.widgets) {
      if (!panelIds.has(widget.id)) {
        const width = 580;
        const height = 440;
        const winWidth = typeof window !== 'undefined' ? window.innerWidth : 1200;
        const winHeight = typeof window !== 'undefined' ? window.innerHeight : 800;
        const x = Math.max(20, Math.round((winWidth - width) / 2));
        const y = Math.max(20, Math.round((winHeight - height) / 2));

        api.addPanel({
          id: widget.id,
          title: widget.title,
          component: DOCK_WIDGET_COMPONENT,
          params: { widgetId: widget.id },
          floating: { width, height, x, y },
        });
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
