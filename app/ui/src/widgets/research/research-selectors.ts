/**
 * Read-only selectors and formatters for Research evidence (FEAT-UI-28).
 *
 * Every function here reshapes or formats values the backend already decided.
 * Nothing in this module derives a score, readiness verdict, classification,
 * p-value, or any other scientific conclusion.
 */

import type {
  ResearchRunDetail,
  ResearchStageView,
  ResearchWarning,
  StageState,
} from "@/clients";

import { STAGE_DEFINITIONS, type StageDefinition } from "./stage-registry";

/** Semantic tone used consistently across badges, bars, and cells. */
export type EvidenceTone =
  | "positive"
  | "negative"
  | "warning"
  | "unknown"
  | "neutral";

/** Human-readable label for each explicit stage state. */
export const STATE_LABELS: Readonly<Record<string, string>> = {
  queued: "Queued",
  running: "Running",
  completed: "Complete",
  partial: "Partial",
  not_selected: "Not selected",
  unavailable: "Unavailable",
  failed: "Failed",
  cancelled: "Cancelled",
  stale: "Stale",
};

/** Tone for each explicit stage state. Colour is never the only cue. */
export const STATE_TONES: Readonly<Record<string, EvidenceTone>> = {
  queued: "neutral",
  running: "neutral",
  completed: "positive",
  partial: "warning",
  not_selected: "unknown",
  unavailable: "unknown",
  failed: "negative",
  cancelled: "warning",
  stale: "warning",
};

/** Tone for each Research-owned readiness value. */
export const READINESS_TONES: Readonly<Record<string, EvidenceTone>> = {
  REVIEW_READY: "positive",
  INSUFFICIENT_EVIDENCE: "warning",
  BLOCKED: "negative",
};

/** Tone for each Research-owned study classification. */
export const CLASSIFICATION_TONES: Readonly<Record<string, EvidenceTone>> = {
  confirmed: "positive",
  contradicted: "negative",
  inconclusive: "warning",
};

/** Read one stage's server-derived state from a run detail. */
export function stageState(
  detail: ResearchRunDetail | null,
  stage: string
): StageState {
  const status = detail?.stage_status?.[stage];
  return (status?.state ?? "queued") as StageState;
}

/** Read the server-supplied reason a stage is in its current state. */
export function stageReason(
  detail: ResearchRunDetail | null,
  stage: string
): string | null {
  return detail?.stage_status?.[stage]?.reason ?? null;
}

/** Stage definitions annotated with their current server-derived state. */
export function annotatedStages(
  detail: ResearchRunDetail | null
): ReadonlyArray<StageDefinition & { state: StageState; reason: string | null }> {
  return STAGE_DEFINITIONS.map((stage) => ({
    ...stage,
    state: stageState(detail, stage.id),
    reason: stageReason(detail, stage.id),
  }));
}

/** Group warnings by their Research-supplied severity, most severe first. */
export function groupWarnings(
  warnings: readonly ResearchWarning[]
): ReadonlyArray<{ severity: string; items: readonly ResearchWarning[] }> {
  const order = ["fatal", "error", "warning", "info"];
  const groups = new Map<string, ResearchWarning[]>();
  for (const warning of warnings) {
    const key = warning.severity || "warning";
    const bucket = groups.get(key);
    if (bucket) bucket.push(warning);
    else groups.set(key, [warning]);
  }
  return [...groups.entries()]
    .map(([severity, items]) => ({ severity, items }))
    .sort((a, b) => {
      const left = order.indexOf(a.severity);
      const right = order.indexOf(b.severity);
      return (left === -1 ? order.length : left) - (right === -1 ? order.length : right);
    });
}

/** Tone for a warning severity. */
export function severityTone(severity: string): EvidenceTone {
  if (severity === "fatal" || severity === "error") return "negative";
  if (severity === "warning") return "warning";
  return "neutral";
}

/** Read one nested evidence branch from a stage view without widening types. */
export function evidenceBranch(
  view: ResearchStageView | null,
  key: string
): Record<string, unknown> | null {
  const branch = view?.evidence?.[key];
  if (branch && typeof branch === "object" && !Array.isArray(branch)) {
    return branch as Record<string, unknown>;
  }
  return null;
}

/** Read one array branch from an evidence record. */
export function evidenceArray(
  source: Record<string, unknown> | null,
  key: string
): unknown[] {
  const value = source?.[key];
  return Array.isArray(value) ? value : [];
}

/** Read one record branch from an evidence record. */
export function evidenceRecord(
  source: Record<string, unknown> | null,
  key: string
): Record<string, unknown> | null {
  const value = source?.[key];
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

/** Coerce an unknown evidence value to a finite number, or null. */
export function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

/** Coerce an unknown evidence value to a display string, or null. */
export function asText(value: unknown): string | null {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return null;
}

/**
 * Format one numeric evidence value for display.
 *
 * Returns an explicit dash for values the backend did not supply, so an
 * unavailable figure never renders as zero.
 */
export function formatNumber(value: unknown, digits = 4): string {
  const parsed = asNumber(value);
  if (parsed === null) return "—";
  if (Number.isInteger(parsed) && Math.abs(parsed) < 1e15) {
    return String(parsed);
  }
  return parsed.toFixed(digits);
}

/**
 * Format a Research-owned score.
 *
 * Scores always render with one decimal so the same value reads identically in
 * the header, the overview, and the scorecard.
 */
export function formatScore(value: unknown): string {
  const parsed = asNumber(value);
  return parsed === null ? "—" : parsed.toFixed(1);
}

/** Format a signed delta, keeping the sign visible. */
export function formatDelta(value: unknown, digits = 4): string {
  const parsed = asNumber(value);
  if (parsed === null) return "—";
  const formatted = Math.abs(parsed) < 1 ? parsed.toFixed(digits) : parsed.toFixed(2);
  return parsed > 0 ? `+${formatted}` : formatted;
}

/** Tone for a delta: positive, negative, or neutral when unchanged/unknown. */
export function deltaTone(value: unknown): EvidenceTone {
  const parsed = asNumber(value);
  if (parsed === null) return "unknown";
  if (parsed > 0) return "positive";
  if (parsed < 0) return "negative";
  return "neutral";
}

/** Format an ISO timestamp for compact display. */
export function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toISOString().replace("T", " ").slice(0, 19);
}

/** Format a duration in milliseconds. */
export function formatDuration(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  if (value < 1000) return `${Math.round(value)} ms`;
  const seconds = value / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${Math.round(seconds % 60)}s`;
}

/** Shorten a content or configuration hash for header display. */
export function hashPrefix(value: string | null | undefined, size = 12): string {
  if (!value) return "—";
  return value.length <= size ? value : `${value.slice(0, size)}…`;
}

/** Format a byte count. */
export function formatBytes(value: number): string {
  if (!Number.isFinite(value)) return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / (1024 * 1024)).toFixed(2)} MiB`;
}

/** Whether a run is still in flight and should keep polling. */
export function isRunActive(status: string | null | undefined): boolean {
  return status === "queued" || status === "running";
}
