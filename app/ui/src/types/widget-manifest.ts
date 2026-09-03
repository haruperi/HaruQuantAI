/**
 * Typed D-UI widget manifest contracts (feature pipeline §4.8).
 *
 * `src/types/` is a documented shared-type support folder: it owns no
 * product registry, no policy, and no runtime behavior. These interfaces
 * describe the typed manifest data every migrating widget feature
 * declares in its `manifest.ts`; manifests are data only and never
 * become a second feature registry.
 */

/** Widget panel placement hint for workspace composition. */
export type WidgetPanel = "left" | "center" | "right" | "bottom";

/** Widget box dimensions in pixels. */
export interface WidgetDimensions {
  readonly width: number;
  readonly height: number;
}

/** One backend subscription a widget's lifecycle depends on. */
export interface WidgetSubscription {
  readonly kind: "sse" | "poll";
  readonly route: string;
  readonly contract: string;
  readonly contractVersion: string;
  readonly capability: string;
}

/** One explicit command a widget can surface. */
export interface WidgetCommand {
  readonly id: string;
  readonly title: string;
  readonly destructive: boolean;
}

/** Accessibility metadata for assistive technology. */
export interface WidgetAccessibility {
  readonly ariaLive: "off" | "polite" | "assertive";
  readonly landmarkRole: string;
  readonly keyboardNavigable: boolean;
}

/** Removal semantics for the widget contribution. */
export interface WidgetRemoval {
  readonly persistedState: "none" | "local";
  readonly description: string;
}

/** Runtime effect declarations for lifecycle ownership. */
export interface WidgetEffects {
  readonly network: boolean;
  readonly browserStorage: boolean;
  readonly systemSettings: boolean;
}

/** Placement metadata for workspace composition. */
export interface WidgetPlacement {
  readonly defaultPanel: WidgetPanel;
  readonly defaultTabGroup?: string;
}

/** Typed D-UI widget manifest owned by exactly one `FEAT-UI-*` feature. */
export interface WidgetManifest {
  /** Owning permanent UI feature identity (e.g. `FEAT-UI-25`). */
  readonly featureId: string;
  /** Registered widget type identity in `WIDGET_TYPES`. */
  readonly widgetType: string;
  /** Widget type schema version, bumped on breaking manifest changes. */
  readonly widgetVersion: number;
  readonly title: string;
  readonly description: string;
  /** Backend/UI capabilities that must be available for active state. */
  readonly requiredCapabilities: readonly string[];
  /** Capabilities that degrade presentation when absent. */
  readonly optionalCapabilities: readonly string[];
  readonly placement: WidgetPlacement;
  readonly defaultDimensions: WidgetDimensions;
  readonly minimumDimensions: WidgetDimensions;
  readonly commands: readonly WidgetCommand[];
  readonly subscriptions: readonly WidgetSubscription[];
  readonly effects: WidgetEffects;
  readonly accessibility: WidgetAccessibility;
  readonly removal: WidgetRemoval;
}
