/**
 * Widget contribution types and contracts for HaruQuantAI D-UI.
 *
 * Every widget contribution in HaruQuantAI is owned by exactly one FEAT-UI-*
 * feature and declares typed manifests and lifecycle adapters.
 */

import type { FC, ReactElement } from "react";
import type { JsonObject, ValidationIssue } from "../contracts/generated/common";
import type {
  TimeDomain,
  WidgetConfigurationEnvelope,
  WidgetInstanceRef,
  WidgetPlacement,
  WidgetRemovalResult,
  WidgetStateEnvelope,
  WidgetTypeDescriptor,
} from "../contracts/generated/ui";

export type {
  TimeDomain,
  WidgetConfigurationEnvelope,
  WidgetInstanceRef,
  WidgetPlacement,
  WidgetRemovalResult,
  WidgetStateEnvelope,
  WidgetTypeDescriptor,
};

/**
 * Standard props provided to any hosted widget component.
 */
export interface WidgetProps<
  TConfig extends JsonObject = JsonObject,
  TState extends JsonObject = JsonObject,
> {
  readonly instance: WidgetInstanceRef;
  readonly placement?: WidgetPlacement;
  readonly configuration: TConfig;
  readonly state: TState;
  readonly onStateChange: (updater: TState | ((prev: TState) => TState)) => void;
  readonly onConfigChange: (updater: TConfig | ((prev: TConfig) => TConfig)) => void;
  readonly isActive?: boolean;
  readonly isMinimized?: boolean;
  readonly isMaximized?: boolean;
  readonly isDirty?: boolean;
  readonly setDirty?: (dirty: boolean) => void;
  readonly onClose?: () => void;
}

/**
 * Lifecycle hooks for widget instances.
 */
export interface WidgetLifecycleHooks<
  TConfig extends JsonObject = JsonObject,
  TState extends JsonObject = JsonObject,
> {
  onMount?: (context: {
    instance: WidgetInstanceRef;
    config: TConfig;
    state: TState;
  }) => void | (() => void);
  onUnmount?: (context: {
    instance: WidgetInstanceRef;
  }) => void;
  validateConfiguration?: (config: TConfig) => ValidationIssue[];
  validateState?: (state: TState) => ValidationIssue[];
  createDefaultConfig?: () => TConfig;
  createDefaultState?: () => TState;
}

/**
 * Complete runtime registration definition for a widget contribution.
 */
export interface WidgetDefinition<
  TConfig extends JsonObject = JsonObject,
  TState extends JsonObject = JsonObject,
> {
  readonly descriptor: WidgetTypeDescriptor;
  readonly component: FC<WidgetProps<TConfig, TState>> | ((props: WidgetProps<TConfig, TState>) => ReactElement | null);
  readonly hooks?: WidgetLifecycleHooks<TConfig, TState>;
}
