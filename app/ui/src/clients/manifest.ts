/** Typed manifest for the removable FEAT-UI-14 backend-client capability. */

/** Stable public capability key provided by the typed transport feature. */
export const TYPED_BACKEND_CAPABILITY = "ui.typed-backend@1" as const;

/** Feature identity and side-effect ownership declaration. */
export const TYPED_BACKEND_MANIFEST = {
  featureId: "FEAT-UI-14",
  featureVersion: 1,
  provides: [TYPED_BACKEND_CAPABILITY] as const,
  requiredCapabilities: [] as const,
  optionalCapabilities: [] as const,
  persistedState: "presentation-only",
  configKeys: [] as const,
} as const;
