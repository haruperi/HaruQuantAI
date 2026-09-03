/**
 * Strict FEAT-UI-25 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; there is no silent
 * pass-through. An empty `symbols` list means the widget derives its
 * symbol set from the authoritative system settings
 * (`MT5_SNAPSHOT_SYMBOLS`) exactly as before the migration.
 */

import { z } from "zod";

/** Persisted widget state schema version (no persisted state today). */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

const symbolSchema = z
  .string()
  .trim()
  .min(1, "symbol must be non-empty")
  .max(32, "symbol must be at most 32 characters")
  .regex(/^[A-Za-z0-9._()+-]+$/, "symbol contains invalid characters");

export const marketTicksConfigSchema = z
  .object({
    /** Observed symbol set; empty derives from system settings. */
    symbols: z.array(symbolSchema).max(200),
    /** Seconds after which the source snapshot reports stale. */
    staleAfterSeconds: z.number().positive().max(3_600),
    /** Seconds after which an individual row reports stale. */
    staleRowAfterSeconds: z.number().positive().max(3_600),
    /** First reconnect delay in milliseconds (exponential backoff base). */
    reconnectInitialDelayMs: z.number().int().min(100).max(10_000),
    /** Reconnect backoff ceiling in milliseconds. */
    reconnectMaxDelayMs: z.number().int().min(1_000).max(60_000),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type MarketTicksConfig = z.infer<typeof marketTicksConfigSchema>;

export const DEFAULT_MARKET_TICKS_CONFIG: MarketTicksConfig = {
  symbols: [],
  staleAfterSeconds: 5,
  staleRowAfterSeconds: 5,
  reconnectInitialDelayMs: 1_000,
  reconnectMaxDelayMs: 10_000,
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value (JSON, storage, or props).
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseMarketTicksConfig(input: unknown): MarketTicksConfig {
  return marketTicksConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * Unknown fields and invalid values still throw; `undefined` selects the
 * defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveMarketTicksConfig(
  input: unknown | undefined,
): MarketTicksConfig {
  if (input === undefined) {
    return DEFAULT_MARKET_TICKS_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseMarketTicksConfig(input);
  }
  return marketTicksConfigSchema.parse({
    ...DEFAULT_MARKET_TICKS_CONFIG,
    ...input,
  });
}
