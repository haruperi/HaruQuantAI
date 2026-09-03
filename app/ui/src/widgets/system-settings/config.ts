/**
 * Strict FEAT-UI-13 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version pin. */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const systemSettingsConfigSchema = z
  .object({
    /** Whether to refresh configuration whenever the modal opens. */
    refreshOnOpen: z.boolean().default(true),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type SystemSettingsConfig = z.infer<typeof systemSettingsConfigSchema>;

export const DEFAULT_SYSTEM_SETTINGS_CONFIG: SystemSettingsConfig = {
  refreshOnOpen: true,
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseSystemSettingsConfig(input: unknown): SystemSettingsConfig {
  return systemSettingsConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveSystemSettingsConfig(
  input: unknown | undefined,
): SystemSettingsConfig {
  if (input === undefined) {
    return DEFAULT_SYSTEM_SETTINGS_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseSystemSettingsConfig(input);
  }
  return systemSettingsConfigSchema.parse({
    ...DEFAULT_SYSTEM_SETTINGS_CONFIG,
    ...input,
  });
}
