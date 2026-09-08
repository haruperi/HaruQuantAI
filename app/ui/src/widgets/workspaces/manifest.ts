/** Typed manifest for the FEAT-UI-COMPOSE_WORKSPACE workspace-layout composition feature. */

/** Workspace layout feature identity and public capability declaration. */
export const WORKSPACE_LAYOUT_MANIFEST = {
  featureId: "FEAT-UI-COMPOSE_WORKSPACE",
  featureVersion: 1,
  provides: ["ui.workspace-layout@1"] as const,
  requiredCapabilities: [] as const,
  optionalCapabilities: [] as const,
  persistedState: "presentation-only",
  persistedStateSchemaVersion: 4,
} as const;
