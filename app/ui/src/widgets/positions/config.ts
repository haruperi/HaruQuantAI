/**
 * Strict FEAT-UI-09 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version pin. */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const positionsConfigSchema = z
  .object({
    /** Default active view tab. */
    defaultTab: z.enum(["positions", "orders"]).default("positions"),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type PositionsConfig = z.infer<typeof positionsConfigSchema>;

export const DEFAULT_POSITIONS_CONFIG: PositionsConfig = {
  defaultTab: "positions",
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parsePositionsConfig(input: unknown): PositionsConfig {
  return positionsConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolvePositionsConfig(
  input: unknown | undefined,
): PositionsConfig {
  if (input === undefined) {
    return DEFAULT_POSITIONS_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parsePositionsConfig(input);
  }
  return positionsConfigSchema.parse({
    ...DEFAULT_POSITIONS_CONFIG,
    ...input,
  });
}
