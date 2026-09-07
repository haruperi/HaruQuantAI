/** Strict, pure persisted-layout configuration and migration for FEAT-UI-01. */

import { z } from "zod";

/** Current Zustand persistence envelope version. */
export const WORKSPACE_LAYOUT_SCHEMA_VERSION = 4 as const;

export const workspaceLayoutConfigSchema = z
  .object({
    persistedStateSchemaVersion: z.literal(WORKSPACE_LAYOUT_SCHEMA_VERSION),
    allowCrossWindowPopout: z.literal(false),
  })
  .strict();

export type WorkspaceLayoutConfig = z.infer<typeof workspaceLayoutConfigSchema>;

export const DEFAULT_WORKSPACE_LAYOUT_CONFIG: WorkspaceLayoutConfig = {
  persistedStateSchemaVersion: WORKSPACE_LAYOUT_SCHEMA_VERSION,
  allowCrossWindowPopout: false,
};

/** Parse workspace configuration without coercion or unknown-field tolerance. */
export function parseWorkspaceLayoutConfig(input: unknown): WorkspaceLayoutConfig {
  return workspaceLayoutConfigSchema.parse(input);
}

/** Resolve documented defaults when no explicit configuration is supplied. */
export function resolveWorkspaceLayoutConfig(
  input: unknown | undefined,
): WorkspaceLayoutConfig {
  if (input === undefined) return DEFAULT_WORKSPACE_LAYOUT_CONFIG;
  if (typeof input !== "object" || input === null) {
    return parseWorkspaceLayoutConfig(input);
  }
  return workspaceLayoutConfigSchema.parse({
    ...DEFAULT_WORKSPACE_LAYOUT_CONFIG,
    ...input,
  });
}
