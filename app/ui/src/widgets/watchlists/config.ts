/**
 * Strict FEAT-UI-03 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version (no persisted state today). */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const watchlistsConfigSchema = z
  .object({
    /** Auto-refresh interval for the watchlist list in seconds. */
    refreshSeconds: z.number().int().min(5).max(600),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type WatchlistsConfig = z.infer<typeof watchlistsConfigSchema>;

export const DEFAULT_WATCHLISTS_CONFIG: WatchlistsConfig = {
  refreshSeconds: 30,
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseWatchlistsConfig(input: unknown): WatchlistsConfig {
  return watchlistsConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveWatchlistsConfig(
  input: unknown | undefined,
): WatchlistsConfig {
  if (input === undefined) {
    return DEFAULT_WATCHLISTS_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseWatchlistsConfig(input);
  }
  return watchlistsConfigSchema.parse({
    ...DEFAULT_WATCHLISTS_CONFIG,
    ...input,
  });
}
