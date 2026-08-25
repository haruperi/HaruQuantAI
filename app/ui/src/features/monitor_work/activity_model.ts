/**
 * Pure domain logic model for activity log snapshots and gap detection.
 *
 * Implements FR-UI-STREAM_ACTIVITY presentation semantics:
 * - Bounded buffer (max cap, drop-oldest with explicit truncation marker)
 * - Sequence jump detection with explicit gap markers (never continuous truth)
 * - Staleness evaluation from snapshot metadata
 * - Pure functions unit-testable without React.
 */

export interface ActivityEvent {
  readonly event_id: string;
  readonly sequence: number;
  readonly timestamp_iso: string;
  readonly severity: "info" | "warning" | "error" | "debug";
  readonly event_type: string;
  readonly message: string;
  readonly correlation_id?: string | null;
  readonly payload?: Record<string, unknown>;
}

export interface ActivityGapMarker {
  readonly type: "gap";
  readonly from_sequence: number;
  readonly to_sequence: number;
  readonly missing_count: number;
}

export interface ActivityTruncationMarker {
  readonly type: "truncation";
  readonly dropped_count: number;
}

export interface ActivityEventEntry {
  readonly type: "event";
  readonly event: ActivityEvent;
}

export type ActivityEntry =
  | ActivityEventEntry
  | ActivityGapMarker
  | ActivityTruncationMarker;

export interface ActivitySnapshot {
  readonly snapshot_id: string;
  readonly cursor: string;
  readonly is_stale: boolean;
  readonly generated_at_iso: string;
  readonly events: readonly ActivityEvent[];
  readonly is_mock?: boolean;
}

export interface IngestResult {
  readonly entries: readonly ActivityEntry[];
  readonly total_events_ingested: number;
  readonly detected_gaps_count: number;
  readonly is_stale: boolean;
  readonly is_truncated: boolean;
  readonly dropped_count: number;
}

export const DEFAULT_BUFFER_CAP = 100;

/**
 * Detect sequence gaps between ordered activity events.
 *
 * Emits an explicit ActivityGapMarker whenever consecutive event sequence
 * numbers jump by more than 1 (FR-UI-STREAM_ACTIVITY).
 */
export function detectGaps(events: readonly ActivityEvent[]): ActivityEntry[] {
  if (!events || events.length === 0) {
    return [];
  }

  // Ensure events are sorted ascending by sequence
  const sorted = [...events].sort((a, b) => a.sequence - b.sequence);
  const result: ActivityEntry[] = [];

  for (let i = 0; i < sorted.length; i++) {
    const current = sorted[i];
    if (i > 0) {
      const prev = sorted[i - 1];
      if (current.sequence > prev.sequence + 1) {
        result.push({
          type: "gap",
          from_sequence: prev.sequence + 1,
          to_sequence: current.sequence - 1,
          missing_count: current.sequence - prev.sequence - 1,
        });
      }
    }
    result.push({
      type: "event",
      event: current,
    });
  }

  return result;
}

/**
 * Check if the activity snapshot is marked stale.
 */
export function isStale(snapshot: ActivitySnapshot | null | undefined): boolean {
  if (!snapshot) {
    return false;
  }
  return snapshot.is_stale === true;
}

/**
 * Ingest a bounded activity snapshot into ordered entries with gap and truncation markers.
 *
 * Capped at maxCap (default 100). When events exceed maxCap, oldest events are dropped
 * and an explicit truncation marker is inserted.
 */
export function ingestSnapshot(
  snapshot: ActivitySnapshot | null | undefined,
  maxCap: number = DEFAULT_BUFFER_CAP
): IngestResult {
  if (!snapshot || !snapshot.events || snapshot.events.length === 0) {
    return {
      entries: [],
      total_events_ingested: 0,
      detected_gaps_count: 0,
      is_stale: isStale(snapshot),
      is_truncated: false,
      dropped_count: 0,
    };
  }

  const rawEvents = snapshot.events;
  const isTruncated = rawEvents.length > maxCap;
  const droppedCount = isTruncated ? rawEvents.length - maxCap : 0;
  const boundedEvents = isTruncated ? rawEvents.slice(droppedCount) : rawEvents;

  const entriesWithGaps = detectGaps(boundedEvents);

  let gapCount = 0;
  for (const entry of entriesWithGaps) {
    if (entry.type === "gap") {
      gapCount++;
    }
  }

  const finalEntries: ActivityEntry[] = [];
  if (isTruncated) {
    finalEntries.push({
      type: "truncation",
      dropped_count: droppedCount,
    });
  }
  finalEntries.push(...entriesWithGaps);

  return {
    entries: finalEntries,
    total_events_ingested: boundedEvents.length,
    detected_gaps_count: gapCount,
    is_stale: isStale(snapshot),
    is_truncated: isTruncated,
    dropped_count: droppedCount,
  };
}
