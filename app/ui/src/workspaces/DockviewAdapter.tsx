/**
 * HaruQuantAI Dockview Adapter.
 *
 * Wraps dockview-react behind a HaruQuantAI-owned adapter, mapping
 * WorkspaceLayoutSnapshot and WidgetInstanceRef to Dockview panels and groups.
 */

import React, { useCallback, useRef } from "react";
import {
  DockviewReact,
  type DockviewReadyEvent,
  type IDockviewPanelProps,
  type DockviewApi,
} from "dockview-react";
import "dockview-react/dist/styles/dockview.css";

import type { WidgetInstanceRef, WidgetPlacement, WorkspaceLayoutSnapshot } from "../contracts/generated/ui";
import { WidgetRegistry } from "../runtime/widget_registry";
import { WidgetHost } from "../runtime/widget_host";

export interface DockviewPanelParams {
  instance: WidgetInstanceRef;
  placement?: WidgetPlacement;
  registry: WidgetRegistry;
  isDirty?: boolean;
  /**
   * Dirty-signal plumb for FR-UI-MANAGE_TABS: a widget state/config change
   * marks its panel dirty until the next successful layout persistence.
   */
  onDirtyChange?: (panelId: string, isDirty: boolean) => void;
}

export interface DockviewAdapterProps {
  registry: WidgetRegistry;
  layout?: WorkspaceLayoutSnapshot | null;
  onReady?: (api: DockviewApi) => void;
  onLayoutChange?: (api: DockviewApi) => void;
  className?: string;
  theme?: string;
}

/**
 * Universal panel component that routes Dockview panel params to WidgetHost.
 */
const DockviewWidgetPanel: React.FC<IDockviewPanelProps<DockviewPanelParams>> = (props) => {
  const params = props.params as DockviewPanelParams | undefined;
  const dirtyRef = React.useRef(false);

  const markDirty = React.useCallback(() => {
    if (!params?.onDirtyChange || dirtyRef.current) return;
    dirtyRef.current = true;
    params.onDirtyChange(params.instance.instance_id, true);
  }, [params]);

  if (!params || !params.instance || !params.registry) {
    return (
      <div style={{ padding: "16px", color: "#64748b" }}>
        Invalid panel parameters.
      </div>
    );
  }

  return (
    <WidgetHost
      instance={params.instance}
      placement={params.placement}
      registry={params.registry}
      onStateChange={markDirty}
      onConfigChange={markDirty}
      onClose={() => props.api.close()}
    />
  );
};

export const DockviewAdapter: React.FC<DockviewAdapterProps> = ({
  registry: _registry,
  layout: _layout,
  onReady,
  onLayoutChange,
  className = "dockview-theme-dark",
  theme = "dockview-theme-dark",
}) => {
  const apiRef = useRef<DockviewApi | null>(null);

  const components = {
    widgetPanel: DockviewWidgetPanel,
  };

  const handleReady = useCallback(
    (event: DockviewReadyEvent) => {
      apiRef.current = event.api;

      // Subscribe to layout changes
      event.api.onDidLayoutChange(() => {
        onLayoutChange?.(event.api);
      });

      onReady?.(event.api);
    },
    [onReady, onLayoutChange]
  );

  return (
    <div
      className={`haru-dockview-wrapper ${className}`}
      style={{ width: "100%", height: "100%", position: "relative" }}
      data-testid="dockview-workspace"
    >
      <DockviewReact
        components={components}
        onReady={handleReady}
        className={theme}
      />
    </div>
  );
};
