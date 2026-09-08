import { z } from "zod";

/**
 * Strict contribution configuration schema for FEAT-UI-REVIEW_DRAFTS.
 *
 * Enforces bounded intervals and validation policy for draft tracking,
 * dirty warning prompts, and irreversible confirmation guards.
 */
export const draftReviewConfigSchema = z
  .object({
    /** Auto-save debounce interval in milliseconds for background drafts. */
    autoSaveIntervalMs: z.number().int().min(500).max(60000).default(2000),
    /** Whether to prompt before discarding forms with unsaved dirty changes. */
    warnOnUnsavedChanges: z.boolean().default(true),
    /** Maximum number of undo/redo draft revisions kept in memory. */
    maxDraftHistory: z.number().int().min(1).max(100).default(20),
    /** Whether to announce validation errors to screen readers via polite live regions. */
    announceErrors: z.boolean().default(true),
    /** Whether irreversible actions require typing an exact confirmation phrase. */
    requireConfirmationWordForIrreversible: z.boolean().default(true),
  })
  .strict();

export type DraftReviewConfig = z.infer<typeof draftReviewConfigSchema>;

export const DEFAULT_DRAFT_REVIEW_CONFIG: DraftReviewConfig = Object.freeze(
  draftReviewConfigSchema.parse({}),
);

/** Parse and strictly validate input configuration. */
export function parseDraftReviewConfig(input: unknown): DraftReviewConfig {
  return draftReviewConfigSchema.parse(input);
}

/** Resolve partial configuration by safely merging with default values. */
export function resolveDraftReviewConfig(
  overrides?: Partial<DraftReviewConfig> | null,
): DraftReviewConfig {
  if (!overrides) return DEFAULT_DRAFT_REVIEW_CONFIG;
  return draftReviewConfigSchema.parse({
    ...DEFAULT_DRAFT_REVIEW_CONFIG,
    ...overrides,
  });
}
