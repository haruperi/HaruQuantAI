import { act, renderHook, waitFor } from "@testing-library/react";
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

describe("useMarketSnapshots — FR-UI-186/187/190", () => {
  beforeEach(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    readSystemMock.mockReset();
    snapshotStreamMock.mockReset();
  });

  it("reads configured symbols and maps an authenticated SSE snapshot", async () => {
    readSystemMock.mockResolvedValue({
      data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD, GBPUSD" } },
    });
    snapshotStreamMock.mockImplementation(async function* () {
      yield {
        sequence: 7,
        payload: {
          source_id: "demo",
          gap: 1,
          stale: false,
          quotes: [{ symbol: "EURUSD", bid: "1.1", ask: "1.2" }],
        },
      };
      await new Promise(() => {});
    });

    const { result, unmount } = renderHook(() => useMarketSnapshots());

    await waitFor(() => expect(result.current.status).toBe("connected"));
    expect(snapshotStreamMock).toHaveBeenCalledWith(
      ["EURUSD", "GBPUSD"],
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    expect(result.current.snapshot).toMatchObject({
      sequence: 7,
      sourceId: "demo",
      gap: 1,
    });
    unmount();
  });

  it("fails visibly when no snapshot symbols are configured", async () => {
    readSystemMock.mockResolvedValue({ data: { settings: {} } });

    const { result } = renderHook(() => useMarketSnapshots());

    await waitFor(() => expect(result.current.status).toBe("unavailable"));
    expect(result.current.error).toContain("not configured");
    expect(snapshotStreamMock).not.toHaveBeenCalled();
  });

  it("releases the stream while hidden and reconnects when visible", async () => {
    readSystemMock.mockResolvedValue({
      data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD" } },
    });
    snapshotStreamMock.mockImplementation(
      (_symbols: string[], options: { signal: AbortSignal }) =>
        (async function* () {
          await new Promise<void>((resolve) => {
            options.signal.addEventListener("abort", () => resolve(), { once: true });
          });
        })(),
    );

    renderHook(() => useMarketSnapshots());
    await waitFor(() => expect(snapshotStreamMock).toHaveBeenCalledTimes(1));

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    act(() => document.dispatchEvent(new Event("visibilitychange")));
    await waitFor(() => {
      const firstSignal = snapshotStreamMock.mock.calls[0][1].signal as AbortSignal;
      expect(firstSignal.aborted).toBe(true);
    });

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    act(() => document.dispatchEvent(new Event("visibilitychange")));
    await waitFor(() => expect(snapshotStreamMock).toHaveBeenCalledTimes(2));
  });
});
