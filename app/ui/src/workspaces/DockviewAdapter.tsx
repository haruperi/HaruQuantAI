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
  const params = props.params;

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
