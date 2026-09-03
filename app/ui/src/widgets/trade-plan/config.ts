/**
 * Strict FEAT-UI-10 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version pin. */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const tradePlanConfigSchema = z
  .object({
    /** Default risk-reward ratio formatted as "X:Y". */
    defaultRiskRewardRatio: z.string().default("3:1"),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type TradePlanConfig = z.infer<typeof tradePlanConfigSchema>;

export const DEFAULT_TRADE_PLAN_CONFIG: TradePlanConfig = {
  defaultRiskRewardRatio: "3:1",
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseTradePlanConfig(input: unknown): TradePlanConfig {
  return tradePlanConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveTradePlanConfig(
  input: unknown | undefined,
): TradePlanConfig {
  if (input === undefined) {
    return DEFAULT_TRADE_PLAN_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseTradePlanConfig(input);
  }
  return tradePlanConfigSchema.parse({
    ...DEFAULT_TRADE_PLAN_CONFIG,
    ...input,
  });
}
