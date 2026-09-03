/**
 * Strict FEAT-UI-05 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version pin. */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const priceLadderConfigSchema = z
  .object({
    /** Default symbol to display on ladder. */
    defaultSymbol: z.string().min(1).default("EURUSD"),
    /** View variant: standalone DOM or embedded trading composition. */
    variant: z.enum(["standalone", "trading"]).default("standalone"),
    /** Optional explicit account identifier. */
    accountId: z.string().optional(),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type PriceLadderConfig = z.infer<typeof priceLadderConfigSchema>;

export const DEFAULT_PRICE_LADDER_CONFIG: PriceLadderConfig = {
  defaultSymbol: "EURUSD",
  variant: "standalone",
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parsePriceLadderConfig(input: unknown): PriceLadderConfig {
  return priceLadderConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolvePriceLadderConfig(
  input: unknown | undefined,
): PriceLadderConfig {
  if (input === undefined) {
    return DEFAULT_PRICE_LADDER_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parsePriceLadderConfig(input);
  }
  return priceLadderConfigSchema.parse({
    ...DEFAULT_PRICE_LADDER_CONFIG,
    ...input,
  });
}
