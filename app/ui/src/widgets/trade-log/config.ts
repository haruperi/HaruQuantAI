/**
 * Strict FEAT-UI-08 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version pin. */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const tradeLogConfigSchema = z
  .object({
    /** Default product filter. */
    defaultProduct: z.string().default("All Products"),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type TradeLogConfig = z.infer<typeof tradeLogConfigSchema>;

export const DEFAULT_TRADE_LOG_CONFIG: TradeLogConfig = {
  defaultProduct: "All Products",
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseTradeLogConfig(input: unknown): TradeLogConfig {
  return tradeLogConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveTradeLogConfig(
  input: unknown | undefined,
): TradeLogConfig {
  if (input === undefined) {
    return DEFAULT_TRADE_LOG_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseTradeLogConfig(input);
  }
  return tradeLogConfigSchema.parse({
    ...DEFAULT_TRADE_LOG_CONFIG,
    ...input,
  });
}
