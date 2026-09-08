"use client";

/** Lifecycle boundary for the FEAT-UI-COMPOSE_WORKSPACE workspace-layout feature. */

import React from "react";

import { resolveWorkspaceLayoutConfig } from "./config";

export interface WorkspaceLayoutFeatureProps {
  readonly children: React.ReactNode;
  readonly config?: unknown;
}

/** Validate workspace configuration before exposing the composition surface. */
export function WorkspaceLayoutFeature({
  children,
  config,
}: WorkspaceLayoutFeatureProps): React.JSX.Element {
  try {
    resolveWorkspaceLayoutConfig(config);
  } catch {
    return (
      <section role="alert" aria-label="Workspace layout configuration error">
        Workspace layout configuration is invalid and was not applied.
      </section>
    );
  }
  return <>{children}</>;
}
