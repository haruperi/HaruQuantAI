/**
 * Typed Widget Registry and Lifecycle Manager for HaruQuantAI D-UI.
 *
 * Implements single-feature ownership enforcement, descriptor validation,
 * lifecycle effect reversal, transactional replacement, and event publication.
 */

import type { JsonObject, ValidationIssue } from "../contracts/generated/common";
import type {
  WidgetLifecycleEvent,
  WidgetRemovalResult,
  WidgetTypeDescriptor,
} from "../contracts/generated/ui";
import type { WidgetDefinition } from "../widgets/types";

export type LifecycleListener = (event: WidgetLifecycleEvent) => void;

export class WidgetRegistryError extends Error {
  constructor(
    message: string,
    public readonly validationIssues: readonly ValidationIssue[] = []
  ) {
    super(message);
    this.name = "WidgetRegistryError";
  }
}

interface MountedInstanceRecord {
  readonly instanceId: string;
  readonly widgetType: string;
  readonly cleanupDisposers: Array<() => void>;
}

export class WidgetRegistry {
  private readonly definitions = new Map<string, WidgetDefinition>();
  private readonly mountedInstances = new Map<string, MountedInstanceRecord>();
  private readonly lifecycleListeners = new Set<LifecycleListener>();

  /**
   * Validate a widget descriptor for structural correctness and authority.
   */
  public validateDescriptor(descriptor: WidgetTypeDescriptor): ValidationIssue[] {
    const issues: ValidationIssue[] = [];

    if (!descriptor.widget_type || descriptor.widget_type.trim() === "") {
      issues.push({
        path: ["widget_type"],
        message: "Widget type module slug is required and cannot be empty",
        code: "REQUIRED_FIELD_MISSING",
      });
    }

    if (!descriptor.owning_feature || descriptor.owning_feature.trim() === "") {
      issues.push({
        path: ["owning_feature"],
        message: "Every widget type must name exactly one owning feature",
        code: "OWNING_FEATURE_REQUIRED",
      });
    } else if (!descriptor.owning_feature.startsWith("FEAT-UI-")) {
      issues.push({
        path: ["owning_feature"],
        message: `Owning feature '${descriptor.owning_feature}' must be a valid FEAT-UI-* capability`,
        code: "INVALID_FEATURE_IDENTIFIER",
      });
    }

    if (descriptor.type_version === undefined || descriptor.type_version < 1) {
      issues.push({
        path: ["type_version"],
        message: "Widget type_version must be an integer >= 1",
        code: "INVALID_TYPE_VERSION",
      });
    }

    if (descriptor.schema_version !== undefined && descriptor.schema_version !== 1) {
      issues.push({
        path: ["schema_version"],
        message: "Schema version must be 1 for v1 wire compatibility",
        code: "INVALID_SCHEMA_VERSION",
      });
    }

    return issues;
  }

  /**
   * Register a typed widget definition.
   *
   * Rejects duplicate registrations and invalid descriptors.
   */
  public registerWidget<TConfig extends JsonObject = JsonObject, TState extends JsonObject = JsonObject>(
    definition: WidgetDefinition<TConfig, TState>
  ): () => void {
    const { descriptor } = definition;
    const issues = this.validateDescriptor(descriptor);
    if (issues.length > 0) {
      throw new WidgetRegistryError(
        `Failed to register widget '${descriptor.widget_type}': validation errors`,
        issues
      );
    }

    if (this.definitions.has(descriptor.widget_type)) {
      throw new WidgetRegistryError(
        `Widget type '${descriptor.widget_type}' is already registered. Use replaceWidget for updates.`
      );
    }

    this.definitions.set(descriptor.widget_type, definition as unknown as WidgetDefinition);
    this.emitLifecycleEvent({
      instance_id: "global",
      widget_type: descriptor.widget_type,
      phase: "REGISTERED",
      schema_version: 1,
    });

    return () => {
      this.unregisterWidget(descriptor.widget_type);
    };
  }

  /**
   * Unregister a widget type, cleanly reversing all effects for any active instances.
   */
  public unregisterWidget(widgetType: string): WidgetRemovalResult {
    const definition = this.definitions.get(widgetType);
    if (!definition) {
      return {
        instance_id: "global",
        widget_type: widgetType,
        removal_state: "REMOVED",
        reversed_effects: [],
        focused_fallback: "shell-workspace-outlet",
        schema_version: 1,
      };
    }

    const reversedEffects: string[] = [];

    // Clean up all mounted instances of this widget type
    for (const [instanceId, record] of Array.from(this.mountedInstances.entries())) {
      if (record.widgetType === widgetType) {
        for (const disposer of record.cleanupDisposers) {
          try {
            disposer();
            reversedEffects.push(`cleanup_instance_${instanceId}`);
          } catch {
            // Ignore error during cleanup to ensure complete reversal
          }
        }
        this.mountedInstances.delete(instanceId);
        this.emitLifecycleEvent({
          instance_id: instanceId,
          widget_type: widgetType,
          phase: "REMOVED",
          schema_version: 1,
        });
      }
    }

    this.definitions.delete(widgetType);
    reversedEffects.push(`unregistered_${widgetType}`);

    this.emitLifecycleEvent({
      instance_id: "global",
      widget_type: widgetType,
      phase: "REMOVED",
      schema_version: 1,
    });

    return {
      instance_id: "global",
      widget_type: widgetType,
      removal_state: "REMOVED",
      reversed_effects: reversedEffects,
      focused_fallback: "shell-workspace-outlet",
      schema_version: 1,
    };
  }

  /**
   * Transactionally replace a widget registration.
   */
  public replaceWidget<TConfig extends JsonObject = JsonObject, TState extends JsonObject = JsonObject>(
    widgetType: string,
    newDefinition: WidgetDefinition<TConfig, TState>
  ): void {
    const issues = this.validateDescriptor(newDefinition.descriptor);
    if (issues.length > 0) {
      throw new WidgetRegistryError(
        `Failed to replace widget '${widgetType}': validation errors in new descriptor`,
        issues
      );
    }

    const existing = this.definitions.get(widgetType);
    if (!existing) {
      this.registerWidget(newDefinition);
      return;
    }

    // Quiesce existing instances
    for (const [instanceId, record] of this.mountedInstances.entries()) {
      if (record.widgetType === widgetType) {
        this.emitLifecycleEvent({
          instance_id: instanceId,
          widget_type: widgetType,
          phase: "QUIESCED",
          schema_version: 1,
        });
      }
    }

    // Replace definition
    this.definitions.set(widgetType, newDefinition as unknown as WidgetDefinition);

    this.emitLifecycleEvent({
      instance_id: "global",
      widget_type: widgetType,
      phase: "REPLACED",
      schema_version: 1,
    });
  }

  /**
   * Register a mounted widget instance and attach its effect disposers.
   */
  public recordMountedInstance(
    instanceId: string,
    widgetType: string,
    disposer?: () => void
  ): () => void {
    let record = this.mountedInstances.get(instanceId);
    if (!record) {
      record = {
        instanceId,
        widgetType,
        cleanupDisposers: [],
      };
      this.mountedInstances.set(instanceId, record);
    }

    if (disposer) {
      record.cleanupDisposers.push(disposer);
    }

    this.emitLifecycleEvent({
      instance_id: instanceId,
      widget_type: widgetType,
      phase: "MOUNTED",
      schema_version: 1,
    });

    return () => {
      this.recordUnmountedInstance(instanceId);
    };
  }

  /**
   * Unmount a specific widget instance, running its registered cleanup effects.
   */
  public recordUnmountedInstance(instanceId: string): void {
    const record = this.mountedInstances.get(instanceId);
    if (!record) return;

    for (const disposer of record.cleanupDisposers) {
      try {
        disposer();
      } catch {
        // Continue cleanup
      }
    }

    this.mountedInstances.delete(instanceId);

    this.emitLifecycleEvent({
      instance_id: instanceId,
      widget_type: record.widgetType,
      phase: "REMOVED",
      schema_version: 1,
    });
  }

  public getWidget(widgetType: string): WidgetDefinition | undefined {
    return this.definitions.get(widgetType);
  }

  public hasWidget(widgetType: string): boolean {
    return this.definitions.has(widgetType);
  }

  public getDescriptors(): WidgetTypeDescriptor[] {
    return Array.from(this.definitions.values()).map((def) => def.descriptor);
  }

  public getDescriptorsByFeature(featureId: string): WidgetTypeDescriptor[] {
    return this.getDescriptors().filter((desc) => desc.owning_feature === featureId);
  }

  public subscribeLifecycleEvents(listener: LifecycleListener): () => void {
    this.lifecycleListeners.add(listener);
    return () => {
      this.lifecycleListeners.delete(listener);
    };
  }

  private emitLifecycleEvent(event: WidgetLifecycleEvent): void {
    for (const listener of this.lifecycleListeners) {
      try {
        listener(event);
      } catch {
        // Prevent listener failures from interrupting registry operations
      }
    }
  }

  public clear(): void {
    for (const widgetType of Array.from(this.definitions.keys())) {
      this.unregisterWidget(widgetType);
    }
    this.definitions.clear();
    this.mountedInstances.clear();
    this.lifecycleListeners.clear();
  }
}
