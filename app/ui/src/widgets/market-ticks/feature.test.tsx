import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError } from "../../clients";
import { WidgetContentHost } from "../../components/layout/WidgetContentHost";
import type { Widget } from "../workspaces";

import { MarketTicksFeature } from "./feature";

const { readSystemMock, snapshotStreamMock } = vi.hoisted(() => ({
  readSystemMock: vi.fn(),
  snapshotStreamMock: vi.fn(),
}));

vi.mock("../../clients", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../clients")>();
  return {
    ...actual,
    apiClients: {
      settings: { readSystem: readSystemMock },
      data: { snapshotStream: snapshotStreamMock },
    },
    unwrapData: (response: { data: unknown }) => response.data,
  };
});

function gatewayUnavailable(): never {
  throw new ApiClientError({
    message: "HTTP 503 opening stream",
    status: 503,
    code: "UPSTREAM_UNAVAILABLE",
  });
}

const SNAPSHOT_EVENT = {
  sequence: 7,
  payload: {
    source_id: "demo",
    gap: 0,
    stale: false,
    quotes: [{ symbol: "EURUSD", timestamp: new Date().toISOString(), bid: "1.085", ask: "1.0852" }],
  },
};

function marketTicksWidget(): Widget {
  return { id: "widget-1", type: "marketTicks", title: "Market Ticks" };
}

describe("FEAT-UI-25 feature adapter — D-UI §4.8 lifecycle", () => {
  beforeEach(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    readSystemMock.mockReset();
    snapshotStreamMock.mockReset();
  });

  it("is active when the backend gateway is present", async () => {
    readSystemMock.mockResolvedValue({
      data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD" } },
    });
    snapshotStreamMock.mockImplementation(async function* () {
      yield SNAPSHOT_EVENT;
      await new Promise(() => {});
    });

    render(<MarketTicksFeature />);

    await waitFor(() => expect(screen.getByText("connected")).toBeInTheDocument());
    expect(screen.getByText("EURUSD")).toBeInTheDocument();
    expect(screen.getByText("1.085")).toBeInTheDocument();
  });

  it("renders the explicit unavailable state when the gateway is absent (503)", async () => {
    readSystemMock.mockResolvedValue({
      data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD" } },
    });
    snapshotStreamMock.mockImplementation(() => {
      gatewayUnavailable();
    });

    render(<MarketTicksFeature />);

    await waitFor(() => expect(screen.getByText("unavailable")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The market ticks gateway is unavailable.",
    );
    expect(screen.queryByText("EURUSD")).not.toBeInTheDocument();
  });

  it("recovers when the gateway returns", async () => {
    readSystemMock.mockResolvedValue({
      data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD" } },
    });
    let calls = 0;
    snapshotStreamMock.mockImplementation(() => {
      calls += 1;
      if (calls === 1) {
        gatewayUnavailable();
      }
      return (async function* () {
        yield SNAPSHOT_EVENT;
        await new Promise(() => {});
      })();
    });

    render(<MarketTicksFeature config={{ reconnectInitialDelayMs: 100, reconnectMaxDelayMs: 1_000 }} />);

    await waitFor(() => expect(screen.getByText("unavailable")).toBeInTheDocument());
    await waitFor(
      () => expect(screen.getByText("connected")).toBeInTheDocument(),
      { timeout: 4_000 },
    );
    expect(screen.getByText("EURUSD")).toBeInTheDocument();
  });

  it("renders symbols-unconfigured as unavailable without inventing rows", async () => {
    readSystemMock.mockResolvedValue({ data: { settings: {} } });

    render(<MarketTicksFeature />);

    await waitFor(() => expect(screen.getByText("unavailable")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("not configured");
    expect(screen.queryByText("EURUSD")).not.toBeInTheDocument();
  });

  it("rejects invalid configuration explicitly without transport activity", () => {
    render(<MarketTicksFeature config={{ symbols: ["EURUSD"], extra: true }} />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.queryByText("Latest quotes")).not.toBeInTheDocument();
    expect(readSystemMock).not.toHaveBeenCalled();
    expect(snapshotStreamMock).not.toHaveBeenCalled();
  });

  it("aborts the subscription exactly on unmount", async () => {
    readSystemMock.mockResolvedValue({
      data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD" } },
    });
    snapshotStreamMock.mockImplementation(
      (_symbols: string[], options: { signal: AbortSignal }) =>
        (async function* () {
          yield SNAPSHOT_EVENT;
          await new Promise<void>((resolve) => {
            options.signal.addEventListener("abort", () => resolve(), { once: true });
          });
        })(),
    );

    const { unmount } = render(<MarketTicksFeature />);
    await waitFor(() =>
      expect(snapshotStreamMock).toHaveBeenCalledTimes(1),
    );
    const signal = snapshotStreamMock.mock.calls[0][1].signal as AbortSignal;
    unmount();
    await waitFor(() => expect(signal.aborted).toBe(true));
  });

  it("suspends the subscription while the document is hidden", async () => {
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

    render(<MarketTicksFeature />);
    await waitFor(() => expect(snapshotStreamMock).toHaveBeenCalledTimes(1));
    const signal = snapshotStreamMock.mock.calls[0][1].signal as AbortSignal;

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    act(() => document.dispatchEvent(new Event("visibilitychange")));

    await waitFor(() => expect(signal.aborted).toBe(true));
    await waitFor(() => expect(screen.getByText("disconnected")).toBeInTheDocument());
  });

  it("registers through the workspace content host", async () => {
    readSystemMock.mockResolvedValue({
      data: { settings: { MT5_SNAPSHOT_SYMBOLS: "EURUSD" } },
    });
    snapshotStreamMock.mockImplementation(async function* () {
      yield SNAPSHOT_EVENT;
      await new Promise(() => {});
    });

    render(<WidgetContentHost widget={marketTicksWidget()} />);

    await waitFor(() =>
      expect(screen.getByText("Latest quotes")).toBeInTheDocument(),
    );
    expect(screen.getByText("EURUSD")).toBeInTheDocument();
  });
});
