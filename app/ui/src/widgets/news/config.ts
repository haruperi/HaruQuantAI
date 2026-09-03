/**
 * Strict FEAT-UI-29 widget configuration (D-UI pipeline §4.8).
 *
 * Unknown fields and invalid values fail loudly; provided fields overlay
 * the documented defaults.
 */

import { z } from "zod";

/** Persisted widget state schema version (no persisted state today). */
export const PERSISTED_STATE_SCHEMA_VERSION = 1 as const;

export const newsConfigSchema = z
  .object({
    /** Default feed language. */
    defaultLanguage: z.enum(["en", "de", "es", "fr", "it", "ja"]),
    /** Whether the embed renders its header. */
    showHeader: z.boolean(),
    /** Persisted state schema version pin. */
    persistedStateSchemaVersion: z.literal(PERSISTED_STATE_SCHEMA_VERSION),
  })
  .strict();

export type NewsConfig = z.infer<typeof newsConfigSchema>;

export const DEFAULT_NEWS_CONFIG: NewsConfig = {
  defaultLanguage: "en",
  showHeader: true,
  persistedStateSchemaVersion: PERSISTED_STATE_SCHEMA_VERSION,
};

/**
 * Parse one strict widget configuration, throwing on unknown fields.
 *
 * @param input - Raw configuration value.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a field is unknown, missing, or invalid.
 */
export function parseNewsConfig(input: unknown): NewsConfig {
  return newsConfigSchema.parse(input);
}

/**
 * Resolve the effective configuration, overlaying provided fields on the
 * documented defaults.
 *
 * @param input - Raw configuration value; `undefined` selects defaults.
 * @returns The validated immutable configuration.
 * @throws z.ZodError when a provided value is invalid.
 */
export function resolveNewsConfig(input: unknown | undefined): NewsConfig {
  if (input === undefined) {
    return DEFAULT_NEWS_CONFIG;
  }
  if (typeof input !== "object" || input === null) {
    return parseNewsConfig(input);
  }
  return newsConfigSchema.parse({ ...DEFAULT_NEWS_CONFIG, ...input });
}
