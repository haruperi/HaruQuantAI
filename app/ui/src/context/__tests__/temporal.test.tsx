import React from "react";
import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { TemporalProvider, useTemporalContext } from "../temporal";

describe("TemporalContext", () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <TemporalProvider workspaceId="test-ws" initialDomain="LIVE" batchWindowMs={0}>
      {children}
    </TemporalProvider>
  );

  it("processes monotonic events and updates cursor and freshness", () => {
    const { result } = renderHook(() => useTemporalContext(), { wrapper });

    act(() => {
      result.current.pushEvent({
        source: {
          source_id: "src-1",
          source_kind: "depth",
          clock_id: "clock-utc",
          schema_version: 1,
        },
        domain: "LIVE",
        sequence: 1,
        asOf: "2026-08-25T12:00:00.000000Z",
        payload: { price: 100 },
      });
    });

    expect(result.current.cursor?.sequence).toBe(1);
    expect(result.current.freshness?.is_stale).toBe(false);
    expect(result.current.openGaps).toHaveLength(0);
  });

  it("detects sequence gaps and records open gaps", () => {
    const { result } = renderHook(() => useTemporalContext(), { wrapper });

    act(() => {
      result.current.pushEvent({
        source: { source_id: "src-1", source_kind: "depth", clock_id: "clock-utc", schema_version: 1 },
        domain: "LIVE",
        sequence: 1,
        asOf: "2026-08-25T12:00:00.000000Z",
        payload: {},
      });
    });

    act(() => {
      result.current.pushEvent({
        source: { source_id: "src-1", source_kind: "depth", clock_id: "clock-utc", schema_version: 1 },
        domain: "LIVE",
        sequence: 5,
        asOf: "2026-08-25T12:00:01.000000Z",
        payload: {},
      });
    });

    expect(result.current.cursor?.sequence).toBe(5);
    expect(result.current.openGaps).toHaveLength(1);
    expect(result.current.openGaps[0]?.from_sequence).toBe(2);
    expect(result.current.openGaps[0]?.to_sequence).toBe(4);
  });

  it("fails closed on incompatible time domain mixing", () => {
    const { result } = renderHook(() => useTemporalContext(), { wrapper });

    act(() => {
      const accepted = result.current.pushEvent({
        source: { source_id: "src-1", source_kind: "depth", clock_id: "clock-utc", schema_version: 1 },
        domain: "PLAYBACK",
        sequence: 1,
        asOf: "2026-08-25T12:00:00.000000Z",
        payload: {},
      });
      expect(accepted).toBe(false);
    });

    expect(result.current.isFailedClosed).toBe(true);
    expect(result.current.resyncState?.outcome).toBe("FAILED_CLOSED");
  });

  it("supports resynchronization recovery", () => {
    const { result } = renderHook(() => useTemporalContext(), { wrapper });

    act(() => {
      result.current.requestResync(10);
    });

    expect(result.current.isFailedClosed).toBe(false);
    expect(result.current.resyncState?.outcome).toBe("RESYNCED");
    expect(result.current.resyncState?.replayed_from_sequence).toBe(10);
  });
});
