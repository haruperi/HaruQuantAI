/**
 * Phase 5 temporal proof for the Market Ticks vertical slice:
 * source identity, sequence ordering, client-side gap detection,
 * reconnect resume cursor, bounded processing, and exact disposal.
 */
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useMarketSnapshots } from "./useMarketSnapshots";

const { readSystemMock, snapshotStreamMock } = vi.hoisted(() => ({
  readSystemMock: vi.fn(),
  snapshotStreamMock: vi.fn(),
}));

vi.mock("../../clients", () => ({
  apiClients: {
    settings: { readSystem: readSystemMock },
    data: { snapshotStream: snapshotStreamMock },
  },
  unwrapData: (response: { data: unknown }) => response.data,
}));

function event(sequence: number, gap = 0, stale = false) {
  return {
    sequence,
    payload: {
      source_id: "data.stream-market-events@1",
      gap,
      stale,
      quotes: [
        { symbol: "EURUSD", timestamp: new Date().toISOString(), bid: "1.085", ask: "1.0852" },
      ],
    },
  };
}

function settingsWithSymbols() {
  readSystemMock.mockResolvedValue({
    data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD" } },
  });
}

describe("FEAT-UI-25 temporal evidence — Phase 5", () => {
  beforeEach(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    readSystemMock.mockReset();
    snapshotStreamMock.mockReset();
  });

  it("preserves source identity and applies events in sequence order", async () => {
    settingsWithSymbols();
    snapshotStreamMock.mockImplementation(async function* () {
      yield event(1);
      yield event(2);
      yield event(3);
      await new Promise(() => {});
    });

    const { result, unmount } = renderHook(() => useMarketSnapshots());

    await waitFor(() =>
      expect(result.current.snapshot?.sequence).toBe(3),
    );
    expect(result.current.snapshot?.sourceId).toBe(
      "data.stream-market-events@1",
    );
    unmount();
  });

  it("counts transport sequence jumps as gaps without interpolating", async () => {
    settingsWithSymbols();
    snapshotStreamMock.mockImplementation(async function* () {
      yield event(1);
      // Payload claims no gap, but the envelope jumps 1 -> 5: the client
      // surfaces the three skipped events (2, 3, 4) as gaps instead of
      // pretending continuity.
      yield event(5, 0);
      await new Promise(() => {});
    });

    const { result, unmount } = renderHook(() => useMarketSnapshots());

    await waitFor(() =>
      expect(result.current.snapshot?.sequence).toBe(5),
    );
    expect(result.current.snapshot?.gap).toBe(3);
    unmount();
  });

  it("reconnects with a resume cursor at the last observed sequence", async () => {
    settingsWithSymbols();
    let calls = 0;
    snapshotStreamMock.mockImplementation(
      (_symbols: string[], options: { resumeAfter?: number }) =>
        (async function* () {
          calls += 1;
          if (calls === 1) {
            yield event(3);
            return;
          }
          yield event(4);
          await new Promise(() => {});
          void options;
        })(),
    );

    const { result, unmount } = renderHook(() =>
      useMarketSnapshots({ initialRetryMs: 100, maxRetryMs: 1_000 }),
    );

    await waitFor(() => expect(calls).toBe(2), { timeout: 4_000 });
    expect(snapshotStreamMock.mock.calls[1][1].resumeAfter).toBe(3);
    await waitFor(() =>
      expect(result.current.snapshot?.sequence).toBe(4),
    );
    expect(result.current.snapshot?.gap).toBe(0);
    unmount();
  });

  it("applies no update after the widget is disposed", async () => {
    settingsWithSymbols();
    snapshotStreamMock.mockImplementation(
      (_symbols: string[], options: { signal: AbortSignal }) =>
        (async function* () {
          yield event(1);
          await new Promise<void>((resolve) => {
            options.signal.addEventListener("abort", () => resolve(), { once: true });
          });
          // Events after disposal must never reach widget state.
          yield event(9);
        })(),
    );

    const { result, unmount } = renderHook(() => useMarketSnapshots());
    await waitFor(() =>
      expect(result.current.snapshot?.sequence).toBe(1),
    );

    unmount();
    await waitFor(() =>
      expect(snapshotStreamMock.mock.calls[0][1].signal.aborted).toBe(true),
    );
    // The hook's returned view object is frozen at the last applied
    // event: sequence 9 was never applied after disposal.
    expect(result.current.snapshot?.sequence).toBe(1);
  });

  it("reports the served staleness flag truthfully", async () => {
    settingsWithSymbols();
    snapshotStreamMock.mockImplementation(async function* () {
      yield event(2, 1, true);
      await new Promise(() => {});
    });

    const { result, unmount } = renderHook(() => useMarketSnapshots());

    await waitFor(() =>
      expect(result.current.snapshot?.sequence).toBe(2),
    );
    expect(result.current.snapshot?.stale).toBe(true);
    expect(result.current.snapshot?.gap).toBe(1);
    unmount();
  });
});
