/**
 * WidgetHost Component for HaruQuantAI D-UI.
 *
 * Hosts a single widget instance inside the workstation canvas, manages its
 * lifecycle, isolates errors via ErrorBoundary, validates configuration and
 * state, and handles missing or incompatible widget types deterministically.
 */

import React, { Component, useEffect, useState, type ErrorInfo, type ReactNode } from "react";
import type { JsonObject } from "../contracts/generated/common";
import type { WidgetInstanceRef, WidgetPlacement } from "../contracts/generated/ui";
import { WidgetRegistry } from "./widget_registry";
import type { WidgetProps } from "../widgets/types";

export interface WidgetHostProps {
  readonly instance: WidgetInstanceRef;
  readonly placement?: WidgetPlacement;
  readonly registry: WidgetRegistry;
  readonly initialConfig?: JsonObject;
  readonly initialState?: JsonObject;
  readonly onConfigChange?: (config: JsonObject) => void;
  readonly onStateChange?: (state: JsonObject) => void;
  readonly onClose?: () => void;
}

interface ErrorBoundaryProps {
  readonly widgetType: string;
  readonly instanceId: string;
  readonly fallback?: ReactNode;
  readonly children: ReactNode;
  readonly onReset?: () => void;
}

interface ErrorBoundaryState {
  readonly hasError: boolean;
  readonly error: Error | null;
}

class WidgetErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(
      `[WidgetErrorBoundary] Widget '${this.props.widgetType}' (instance ${this.props.instanceId}) crashed:`,
      error,
      errorInfo
    );
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div
          className="widget-host-error-panel"
          role="alert"
          style={{
            padding: "16px",
            border: "1px solid #e11d48",
            borderRadius: "6px",
            backgroundColor: "#fff1f2",
            color: "#9f1239",
            margin: "8px",
          }}
        >
          <h4 style={{ margin: "0 0 8px 0" }}>Widget Rendering Error</h4>
          <p style={{ margin: "0 0 8px 0", fontSize: "13px" }}>
            Widget <strong>{this.props.widgetType}</strong> encountered an unhandled error:
          </p>
          <pre
            style={{
              padding: "8px",
              backgroundColor: "#ffe4e6",
              borderRadius: "4px",
              fontSize: "11px",
              overflow: "auto",
              maxHeight: "120px",
            }}
          >
            {this.state.error?.message || "Unknown error"}
          </pre>
          <button
            type="button"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              this.props.onReset?.();
            }}
            style={{
              marginTop: "8px",
              padding: "4px 12px",
              backgroundColor: "#e11d48",
              color: "#ffffff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "12px",
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export const MissingWidgetPlaceholder: React.FC<{
  widgetType: string;
  instanceId: string;
  onRemove?: () => void;
}> = ({ widgetType, instanceId, onRemove }) => (
  <div
    className="widget-host-missing-placeholder"
    role="status"
    style={{
      padding: "16px",
      border: "1px dashed #94a3b8",
      borderRadius: "6px",
      backgroundColor: "#f8fafc",
      color: "#475569",
      textAlign: "center",
      margin: "8px",
    }}
  >
    <h4 style={{ margin: "0 0 8px 0", color: "#334155" }}>Missing Widget Provider</h4>
    <p style={{ margin: "0 0 8px 0", fontSize: "13px" }}>
      The widget type <code>{widgetType}</code> is not registered or its feature is unavailable.
    </p>
    <span style={{ fontSize: "11px", color: "#64748b", display: "block", marginBottom: "12px" }}>
      Instance: {instanceId}
    </span>
    {onRemove && (
      <button
        type="button"
        onClick={onRemove}
        style={{
          padding: "4px 12px",
          backgroundColor: "#f1f5f9",
          border: "1px solid #cbd5e1",
          borderRadius: "4px",
          cursor: "pointer",
          fontSize: "12px",
          color: "#334155",
        }}
      >
        Remove Missing Widget
      </button>
    )}
  </div>
);

export const WidgetHost: React.FC<WidgetHostProps> = ({
  instance,
  placement,
  registry,
  initialConfig = {},
  initialState = {},
  onConfigChange,
  onStateChange,
  onClose,
}) => {
  const definition = registry.getWidget(instance.widget_type);
  const [config, setConfig] = useState<JsonObject>(() => {
    if (Object.keys(initialConfig).length > 0) return initialConfig;
    return definition?.hooks?.createDefaultConfig?.() || {};
  });
  const [state, setState] = useState<JsonObject>(() => {
    if (Object.keys(initialState).length > 0) return initialState;
    return definition?.hooks?.createDefaultState?.() || {};
  });
  const [isDirty, setIsDirty] = useState<boolean>(false);

  // Mount/Unmount lifecycle tracking with exact effect reversal
  useEffect(() => {
    if (!definition) return;

    let cleanupFn: (() => void) | void = undefined;
    if (definition.hooks?.onMount) {
      cleanupFn = definition.hooks.onMount({
        instance,
        config,
        state,
      });
    }

    const unregisterMounted = registry.recordMountedInstance(
      instance.instance_id,
      instance.widget_type,
      () => {
        if (typeof cleanupFn === "function") {
          cleanupFn();
        }
        if (definition.hooks?.onUnmount) {
          definition.hooks.onUnmount({ instance });
        }
      }
    );

    return () => {
      unregisterMounted();
    };
  }, [instance.instance_id, instance.widget_type, definition, registry]);

  const handleStateUpdate = (updater: JsonObject | ((prev: JsonObject) => JsonObject)) => {
    setState((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      onStateChange?.(next);
      return next;
    });
  };

  const handleConfigUpdate = (updater: JsonObject | ((prev: JsonObject) => JsonObject)) => {
    setConfig((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      onConfigChange?.(next);
      return next;
    });
  };

  if (!definition) {
    return (
      <MissingWidgetPlaceholder
        widgetType={instance.widget_type}
        instanceId={instance.instance_id}
        onRemove={onClose}
      />
    );
  }

  const widgetProps: WidgetProps = {
    instance,
    placement,
    configuration: config,
    state,
    onStateChange: handleStateUpdate,
    onConfigChange: handleConfigUpdate,
    isActive: true,
    isMinimized: placement?.is_minimized ?? false,
    isMaximized: placement?.is_maximized ?? false,
    isDirty,
    setDirty: setIsDirty,
    onClose,
  };

  return (
    <WidgetErrorBoundary
      widgetType={instance.widget_type}
      instanceId={instance.instance_id}
    >
      <div
        className="haru-widget-container"
        data-widget-type={instance.widget_type}
        data-instance-id={instance.instance_id}
        data-owning-feature={definition.descriptor.owning_feature}
        role="region"
        aria-label={`${definition.descriptor.widget_type} widget`}
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          overflow: "auto",
        }}
      >
        {React.createElement(definition.component, widgetProps)}
      </div>
    </WidgetErrorBoundary>
  );
};
