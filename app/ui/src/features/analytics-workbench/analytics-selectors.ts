/**
 * Analytics presentation selectors (FEAT-UI-32).
 *
 * These helpers project owner comparison evidence into rows a table can
 * render. They never subtract, rank, or otherwise combine two runs: a
 * difference between runs is a comparison the Analytics owner performs, and a
 * browser-side subtraction of arbitrary JSON would silently invent one.
 */

import type { ComparisonEvidence } from "@/clients";

/** Maximum runs the comparison surface will select at once. */
export const MAX_COMPARISON_RUNS = 8;

/** Minimum runs required before a comparison can be requested. */
export const MIN_COMPARISON_RUNS = 2;

/** One presentation row of owner comparison evidence. */
export interface ComparisonRow {
  runId: string;
  label: string;
  value: string | null;
  unit: string | null;
  context: string;
}

/** Read one field from an owner comparison entry. */
function field(entry: Record<string, unknown>, key: string): unknown {
  return entry[key];
}

/**
 * Project owner comparison evidence into presentation rows.
 *
 * Args:
 *   evidence: Owner-produced comparison payload.
 *
 * Returns:
 *   One row per run the owner reported, in the owner's order.
 */
export function toComparisonRows(
  evidence: ComparisonEvidence | null | undefined,
): ComparisonRow[] {
  if (!evidence) return [];
  return evidence.runs.map((entry) => {
    const value = field(entry, "value");
    const unit = field(entry, "unit");
    const label = field(entry, "label");
    const runId = field(entry, "run_id");
    const context = field(entry, "source_context");
    return {
      runId: typeof runId === "string" ? runId : "",
      label: typeof label === "string" ? label : evidence.metric,
      value:
        value === null || value === undefined || value === ""
          ? null
          : String(value),
      unit: typeof unit === "string" ? unit : null,
      context: typeof context === "string" ? context : "all",
    };
  });
}

/**
 * Return whether a selection can be compared.
 *
 * Args:
 *   runIds: Currently selected run identities.
 *
 * Returns:
 *   True when the selection is within the comparison bounds.
 */
export function isComparable(runIds: readonly string[]): boolean {
  return (
    runIds.length >= MIN_COMPARISON_RUNS &&
    runIds.length <= MAX_COMPARISON_RUNS
  );
}

/**
 * Add or remove one run from a bounded selection.
 *
 * Args:
 *   runIds: Current selection.
 *   runId: Run identity to toggle.
 *
 * Returns:
 *   The updated selection, bounded to the maximum.
 */
export function toggleSelection(
  runIds: readonly string[],
  runId: string,
): string[] {
  if (runIds.includes(runId)) {
    return runIds.filter((item) => item !== runId);
  }
  if (runIds.length >= MAX_COMPARISON_RUNS) {
    return [...runIds];
  }
  return [...runIds, runId];
}
