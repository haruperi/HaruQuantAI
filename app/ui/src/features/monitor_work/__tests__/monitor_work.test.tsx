import { describe, it, expect } from "vitest";
import {
  SPEC,
  createFeature,
  detectGaps,
  ingestSnapshot,
  isStale,
  type ActivityEvent,
  type ActivitySnapshot,
} from "../index";
import { MockUiPresentationProvider } from "../../../mocks/mock_provider";

function makeEvent(sequence: number, overrides: Partial<ActivityEvent> = {}): ActivityEvent {
  return {
    event_id: `evt-test-${sequence}`,
    sequence,
    timestamp_iso: "2026-08-26T00:00:00.000000Z",
    severity: "info",
    event_type: "JOB_PROGRESS",
    message: `Progress event ${sequence}`,
    correlation_id: "job-100",
    ...overrides,
  };
}

describe("FEAT-UI-MONITOR_WORK feature and activity model (FR-UI-STREAM_ACTIVITY)", () => {
  it("registers the feature manifest with the ratified capability", () => {
    expect(SPEC.featureId).toBe("FEAT-UI-MONITOR_WORK");
    expect(SPEC.providesCapabilities).toContain("ui.monitor-work@1");

    const client = new MockUiPresentationProvider();
    const feature = createFeature({ presentationClient: client });
    expect(feature.manifest.featureId).toBe("FEAT-UI-MONITOR_WORK");
  });

  describe("detectGaps pure function", () => {
    it("returns empty array for empty or null event list", () => {
      expect(detectGaps([])).toEqual([]);
    });

    it("detects no gaps for continuous sequence numbers", () => {
      const events = [makeEvent(1), makeEvent(2), makeEvent(3)];
      const entries = detectGaps(events);
      expect(entries).toHaveLength(3);
      expect(entries.every((e) => e.type === "event")).toBe(true);
    });

    it("inserts explicit gap markers for sequence jumps (R32 / FR-UI-STREAM_ACTIVITY)", () => {
      const events = [
        makeEvent(10),
        makeEvent(11),
        makeEvent(15), // jump of 4 (missing 12, 13, 14)
        makeEvent(17), // jump of 2 (missing 16)
      ];
      const entries = detectGaps(events);
      expect(entries).toHaveLength(6); // 4 events + 2 gaps

      expect(entries[0]).toEqual({ type: "event", event: events[0] });
      expect(entries[1]).toEqual({ type: "event", event: events[1] });
      expect(entries[2]).toEqual({
        type: "gap",
        from_sequence: 12,
        to_sequence: 14,
        missing_count: 3,
      });
      expect(entries[3]).toEqual({ type: "event", event: events[2] });
      expect(entries[4]).toEqual({
        type: "gap",
        from_sequence: 16,
        to_sequence: 16,
        missing_count: 1,
      });
      expect(entries[5]).toEqual({ type: "event", event: events[3] });
    });
  });

  describe("isStale pure function", () => {
    it("returns false for undefined or fresh snapshots", () => {
      expect(isStale(undefined)).toBe(false);
      expect(isStale(null)).toBe(false);
      expect(
        isStale({
          snapshot_id: "snap-1",
          cursor: "c1",
          is_stale: false,
          generated_at_iso: "2026-08-26T00:00:00Z",
          events: [],
        })
      ).toBe(false);
    });

    it("returns true when snapshot is marked stale", () => {
      expect(
        isStale({
          snapshot_id: "snap-1",
          cursor: "c1",
          is_stale: true,
          generated_at_iso: "2026-08-26T00:00:00Z",
          events: [],
        })
      ).toBe(true);
    });
  });

  describe("ingestSnapshot buffer bounding and truncation", () => {
    it("handles empty snapshots safely", () => {
      const result = ingestSnapshot(null);
      expect(result.entries).toEqual([]);
      expect(result.total_events_ingested).toBe(0);
      expect(result.is_truncated).toBe(false);
      expect(result.is_stale).toBe(false);
    });

    it("bounds buffer at maxCap and prepends truncation marker", () => {
      const events = [
        makeEvent(1),
        makeEvent(2),
        makeEvent(3),
        makeEvent(4),
        makeEvent(5),
      ];
      const snapshot: ActivitySnapshot = {
        snapshot_id: "snap-cap",
        cursor: "c5",
        is_stale: false,
        generated_at_iso: "2026-08-26T00:00:00Z",
        events,
      };

      const result = ingestSnapshot(snapshot, 3);
      expect(result.is_truncated).toBe(true);
      expect(result.dropped_count).toBe(2);
      expect(result.total_events_ingested).toBe(3);

      // First entry is truncation marker
      expect(result.entries[0]).toEqual({
        type: "truncation",
        dropped_count: 2,
      });

      // Retained events are sequences 3, 4, 5
      expect(result.entries.slice(1)).toEqual([
        { type: "event", event: events[2] },
        { type: "event", event: events[3] },
        { type: "event", event: events[4] },
      ]);
    });
  });
});
