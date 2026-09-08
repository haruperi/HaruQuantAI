/**
 * Strict contribution configuration schema for FEAT-UI-VIEW_COLLECTIONS.
 */

import { z } from "zod";

export const COLLECTION_GRID_SCHEMA_VERSION = 1 as const;

export const collectionGridConfigSchema = z
  .object({
    persistedStateSchemaVersion: z.literal(COLLECTION_GRID_SCHEMA_VERSION).default(COLLECTION_GRID_SCHEMA_VERSION),
    pageSize: z.number().int().min(1).max(1000).default(50),
    virtualRowHeight: z.number().int().min(20).max(120).default(36),
    overscanCount: z.number().int().min(0).max(30).default(5),
    updateCoalesceMs: z.number().int().min(10).max(500).default(50),
    maxPreviewRows: z.number().int().min(1).max(1000).default(100),
  })
  .strict();

export type CollectionGridConfig = z.infer<typeof collectionGridConfigSchema>;

export const DEFAULT_COLLECTION_GRID_CONFIG: CollectionGridConfig = {
  persistedStateSchemaVersion: COLLECTION_GRID_SCHEMA_VERSION,
  pageSize: 50,
  virtualRowHeight: 36,
  overscanCount: 5,
  updateCoalesceMs: 50,
  maxPreviewRows: 100,
};

/** Parse grid configuration without coercion or unknown-field tolerance. */
export function parseCollectionGridConfig(input: unknown): CollectionGridConfig {
  return collectionGridConfigSchema.parse(input);
}

/** Resolve documented defaults when no explicit configuration is supplied. */
export function resolveCollectionGridConfig(input: unknown | undefined): CollectionGridConfig {
  if (input === undefined) return DEFAULT_COLLECTION_GRID_CONFIG;
  if (typeof input !== "object" || input === null) {
    return parseCollectionGridConfig(input);
  }
  return collectionGridConfigSchema.parse({
    ...DEFAULT_COLLECTION_GRID_CONFIG,
    ...input,
  });
}
