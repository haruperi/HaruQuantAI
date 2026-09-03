/**
 * Strict FEAT-UI-02 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version (no persisted state today). */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const marketsConfigSchema = z
  .object({
    /** Directory page size per request. */
    pageSize: z.number().int().min(1).max(200),
    /** Maximum directory pages fetched per load (anti-walk cap). */
    maxPages: z.number().int().min(1).max(10),
    /** Seconds the loader waits before opening the live stream. */
    streamSettlingSeconds: z.number().int().min(1).max(60),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type MarketsConfig = z.infer<typeof marketsConfigSchema>;

export const DEFAULT_MARKETS_CONFIG: MarketsConfig = {
  pageSize: 50,
  maxPages: 4,
  streamSettlingSeconds: 10,
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseMarketsConfig(input: unknown): MarketsConfig {
  return marketsConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveMarketsConfig(
  input: unknown | undefined,
): MarketsConfig {
  if (input === undefined) {
    return DEFAULT_MARKETS_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseMarketsConfig(input);
  }
  return marketsConfigSchema.parse({ ...DEFAULT_MARKETS_CONFIG, ...input });
}
