import { describe, it, expect } from "vitest";
import { WidgetRegistry, WidgetRegistryError } from "../widget_registry";
import type { WidgetDefinition } from "../../widgets/types";

describe("WidgetRegistry", () => {
  it("registers a valid widget descriptor and emits REGISTERED event", () => {
    const registry = new WidgetRegistry();
    const events: any[] = [];
    registry.subscribeLifecycleEvents((e) => events.push(e));

    const definition: WidgetDefinition = {
      descriptor: {
        widget_type: "test_widget",
        owning_feature: "FEAT-UI-RUN_RESEARCH",
        type_version: 1,
        schema_version: 1,
      },
      component: () => null,
    };

    const unregister = registry.registerWidget(definition);
    expect(registry.hasWidget("test_widget")).toBe(true);
    expect(registry.getWidget("test_widget")).toBe(definition);
    expect(events).toHaveLength(1);
    expect(events[0].phase).toBe("REGISTERED");

    unregister();
    expect(registry.hasWidget("test_widget")).toBe(false);
  });

  it("rejects descriptors with invalid or missing owning feature", () => {
    const registry = new WidgetRegistry();

    expect(() =>
      registry.registerWidget({
        descriptor: {
          widget_type: "invalid_widget",
          owning_feature: "",
          type_version: 1,
          schema_version: 1,
        },
        component: () => null,
      })
    ).toThrow(WidgetRegistryError);

    expect(() =>
      registry.registerWidget({
        descriptor: {
          widget_type: "invalid_widget_2",
          owning_feature: "NOT_A_FEAT_UI",
          type_version: 1,
          schema_version: 1,
        },
        component: () => null,
      })
    ).toThrow(WidgetRegistryError);
  });

  it("rejects duplicate registrations", () => {
    const registry = new WidgetRegistry();
    const definition: WidgetDefinition = {
      descriptor: {
        widget_type: "dup_widget",
        owning_feature: "FEAT-UI-EDIT_CODE",
        type_version: 1,
        schema_version: 1,
      },
      component: () => null,
    };

    registry.registerWidget(definition);
    expect(() => registry.registerWidget(definition)).toThrow(WidgetRegistryError);
  });

  it("reverses instance effects upon unregistering a widget type", () => {
    const registry = new WidgetRegistry();
    registry.registerWidget({
      descriptor: {
        widget_type: "effect_widget",
        owning_feature: "FEAT-UI-MANAGE_DATA",
        type_version: 1,
        schema_version: 1,
      },
      component: () => null,
    });

    let cleanedUp = false;
    registry.recordMountedInstance("inst-1", "effect_widget", () => {
      cleanedUp = true;
    });

    const result = registry.unregisterWidget("effect_widget");
    expect(cleanedUp).toBe(true);
    expect(result.removal_state).toBe("REMOVED");
    expect(result.reversed_effects).toContain("cleanup_instance_inst-1");
    expect(result.reversed_effects).toContain("unregistered_effect_widget");
  });

  it("transactionally replaces a widget registration with quiesce", () => {
    const registry = new WidgetRegistry();
    const events: any[] = [];
    registry.subscribeLifecycleEvents((e) => events.push(e));

    registry.registerWidget({
      descriptor: {
        widget_type: "replace_me",
        owning_feature: "FEAT-UI-OPERATE_TRADING",
        type_version: 1,
        schema_version: 1,
      },
      component: () => null,
    });

    registry.recordMountedInstance("inst-2", "replace_me");

    const newDef: WidgetDefinition = {
      descriptor: {
        widget_type: "replace_me",
        owning_feature: "FEAT-UI-OPERATE_TRADING",
        type_version: 2,
        schema_version: 1,
      },
      component: () => null,
    };

    registry.replaceWidget("replace_me", newDef);
    expect(registry.getWidget("replace_me")?.descriptor.type_version).toBe(2);

    const phases = events.map((e) => e.phase);
    expect(phases).toContain("QUIESCED");
    expect(phases).toContain("REPLACED");
  });
});
