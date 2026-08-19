/**
 * Simulation workbench selectors and helper predicates (FEAT-UI-31).
 *
 * These selectors normalise run and batch state into reusable boolean/percentage
 * helpers. They intentionally do not derive policies or UI labels; those remain
 * server-authoritative.
 */

import type {
  BacktestRun,
  BatchProjection,
  CatalogueStatus,
} from "@/clients";

/** Canonical run lifecycle states that still need polling. */
export const ACTIVE_RUN_STATUSES: ReadonlySet<string> = new Set(["queued", "running"]);

/** Batch lifecycle states that still need polling or operator action. */
export const ACTIVE_BATCH_STATUSES: ReadonlySet<string> = new Set([
  "queued",
  "running",
]);

/** Stream connection lifecycle used by monitor components. */
export type StreamState =
  | "idle"
  | "connecting"
  | "open"
  | "closed"
  | "error"
  | "settled";

/** Return true when a canonical run has not reached a terminal status. */
export function isRunActive(run: BacktestRun | null | undefined): boolean {
  if (!run) return false;
  return ACTIVE_RUN_STATUSES.has(run.status);
}

/** Return true when a batch is still in-flight. */
export function isBatchActive(status: CatalogueStatus | null | undefined): boolean {
  if (!status) return false;
  return ACTIVE_BATCH_STATUSES.has(status);
}

/** Return true when a canonical run reached terminal state. */
export function isRunSettled(run: BacktestRun | null | undefined): boolean {
  if (!run) return false;
  return !isRunActive(run);
}

/** Return the ratio of done items to total items as a percentage. */
export function batchCompletionRatio(batch: BatchProjection | null | undefined): number {
  if (!batch || batch.total_items <= 0) return 0;
  const done = batch.completed_items + batch.failed_items + batch.cancelled_items;
  return Math.min(100, Math.round((done / batch.total_items) * 100));
}
