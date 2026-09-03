/**
 * Strict FEAT-UI-06 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version pin. */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const tradingConfigSchema = z
  .object({
    /** Default symbol to populate on mount. */
    defaultSymbol: z.string().min(1).default("EURUSD"),
    /** When true, only mounts the ticket pane without the side ladder. */
    ticketHostOnly: z.boolean().default(false),
    /** Optional pre-bound account identifier. */
    accountId: z.string().optional(),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type TradingConfig = z.infer<typeof tradingConfigSchema>;

export const DEFAULT_TRADING_CONFIG: TradingConfig = {
  defaultSymbol: "EURUSD",
  ticketHostOnly: false,
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseTradingConfig(input: unknown): TradingConfig {
  return tradingConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveTradingConfig(input: unknown | undefined): TradingConfig {
  if (input === undefined) {
    return DEFAULT_TRADING_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseTradingConfig(input);
  }
  return tradingConfigSchema.parse({
    ...DEFAULT_TRADING_CONFIG,
    ...input,
  });
}
