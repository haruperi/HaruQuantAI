/** Typed manifest for the removable FEAT-UI-SESSION_ACCESS contribution. */

import type { MetadataRoute } from "next";

/** Stable public capability key provided by the session access feature. */
export const SESSION_ACCESS_CAPABILITY = "ui.access-gate@1" as const;

/** Feature identity, dependencies, and side-effect ownership declaration. */
export const SESSION_ACCESS_MANIFEST = {
  featureId: "FEAT-UI-SESSION_ACCESS",
  featureVersion: 1,
  provides: [SESSION_ACCESS_CAPABILITY] as const,
  requiredCapabilities: ["ui.typed-backend@1"] as const,
  optionalCapabilities: ["interfaces.operate-identity@1"] as const,
  persistedState: "presentation-only",
  configKeys: [] as const,
} as const;

/** Existing-app web manifest required by Next's reserved `app/manifest.ts` path. */
export default function applicationManifest(): MetadataRoute.Manifest {
  return {
    name: "HaruQuantAI",
    short_name: "HaruQuantAI",
    description: "Research and trading simulation workstation",
    start_url: "/",
    display: "standalone",
    background_color: "#0a0a0a",
    theme_color: "#0a0a0a",
  };
}
