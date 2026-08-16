import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useDepthStream } from "./useDepthStream";

const { depthStreamMock } = vi.hoisted(() => ({
  depthStreamMock: vi.fn(),
}));

vi.mock("../../clients", () => ({
  apiClients: {
    data: { depthStream: depthStreamMock },
  },
}));

describe("useDepthStream — FR-UI-055/056", () => {
  beforeEach(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    depthStreamMock.mockReset();
  });

  it("maps a real depth event's book for the requested symbol only", async () => {
    depthStreamMock.mockImplementation(async function* () {
      yield {
        sequence: 3,
        payload: {
          stale: false,
          gap: 0,
          source_id: "mt5",
          books: [
            {
              symbol: "EURUSD",
              book_depth: 2,
              bids: [{ price: "1.1000", volume: "50" }],
              asks: [{ price: "1.1002", volume: "40" }],
            },
            {
              symbol: "GBPUSD",
              book_depth: 1,
              bids: [{ price: "1.3", volume: "10" }],
              asks: [],
            },
          ],
          errors: [],
        },
      };
      await new Promise(() => {});
    });

    const { result, unmount } = renderHook(() => useDepthStream("EURUSD"));

    await waitFor(() => expect(result.current.status).toBe("connected"));
    expect(depthStreamMock).toHaveBeenCalledWith(
      ["EURUSD"],
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    expect(result.current.book).toMatchObject({
      symbol: "EURUSD",
      bids: [{ price: 1.1, volume: 50 }],
      asks: [{ price: 1.1002, volume: 40 }],
      error: null,
    });
    expect(result.current.sequence).toBe(3);
    unmount();
  });

  it("surfaces a real per-symbol book error rather than an empty book", async () => {
    depthStreamMock.mockImplementation(async function* () {
      yield {
        sequence: 1,
        payload: {
          stale: false,
          gap: 0,
          source_id: "mt5",
          books: [],
          errors: [{ symbol: "EURUSD", code: 4301 }],
        },
      };
      await new Promise(() => {});
    });

    const { result, unmount } = renderHook(() => useDepthStream("EURUSD"));

    await waitFor(() => expect(result.current.book).not.toBeNull());
    expect(result.current.book).toMatchObject({
      symbol: "EURUSD",
      bids: [],
      asks: [],
      error: { code: 4301 },
    });
    unmount();
  });

  it("never opens a stream when no symbol is supplied", async () => {
    const { result } = renderHook(() => useDepthStream(""));

    await waitFor(() => expect(result.current.status).toBe("unavailable"));
    expect(depthStreamMock).not.toHaveBeenCalled();
  });

  it("releases the stream while hidden and reconnects when visible", async () => {
    depthStreamMock.mockImplementation(
      (_symbols: string[], options: { signal: AbortSignal }) =>
        (async function* () {
          await new Promise<void>((resolve) => {
            options.signal.addEventListener("abort", () => resolve(), { once: true });
          });
        })(),
    );

    renderHook(() => useDepthStream("EURUSD"));
    await waitFor(() => expect(depthStreamMock).toHaveBeenCalledTimes(1));

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    act(() => document.dispatchEvent(new Event("visibilitychange")));
    await waitFor(() => {
      const firstSignal = depthStreamMock.mock.calls[0][1].signal as AbortSignal;
      expect(firstSignal.aborted).toBe(true);
    });

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    act(() => document.dispatchEvent(new Event("visibilitychange")));
    await waitFor(() => expect(depthStreamMock).toHaveBeenCalledTimes(2));
  });
});
