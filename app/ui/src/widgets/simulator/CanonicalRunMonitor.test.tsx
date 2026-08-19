/**
 * Unit tests for canonical run monitor behavior (FEAT-UI-31, P2-T01).
 *
 * Covers authoritative load, cancellation, ordered progress rendering, the
 * canonical Analytics handoff, and the rule that a disconnect is never treated
 * as a successful terminal outcome.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { runById, cancelRun, streamEvents } = vi.hoisted(() => ({
  runById: vi.fn(),
  cancelRun: vi.fn(),
  streamEvents: { current: [] as { sequence: number; payload: unknown }[] },
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    simulator: {
      run: runById,
      cancelRun,
    },
  },
}));

vi.mock("@/context/streams", () => ({
  consumeStream: () => ({
    async *[Symbol.asyncIterator]() {
      for (const event of streamEvents.current) {
        yield event;
      }
    },
  }),
}));

vi.mock("@/clients/routes", () => ({
  simulatorRoutes: {
    runStream: { id: "api.simulator.run_stream" },
  },
}));

vi.mock("./simulation-store", () => {
  const setCanonicalRunId = vi.fn();
  const setCanonicalRunState = vi.fn();
  return {
    useSimulationWorkbenchStore: (selector: (state: {
      setCanonicalRunId: typeof setCanonicalRunId;
      setCanonicalRunState: typeof setCanonicalRunState;
    }) => unknown) => selector({ setCanonicalRunId, setCanonicalRunState }),
  };
});

import { CanonicalRunMonitor } from "./CanonicalRunMonitor";

const RUN = {
  job_id: "run-123",
  status: "queued",
  stage: null,
  submitted_at: "2026-08-18T10:00:00Z",
  started_at: "2026-08-18T10:00:01Z",
  finished_at: null,
  symbol: "EURUSD",
  timeframe: "H1",
  strategy_id: "trend",
  events: [],
  result: null,
  error: null,
};

const SUCCEEDED = {
  ...RUN,
  status: "succeeded",
  stage: "analytics",
  finished_at: "2026-08-18T10:04:00Z",
  events: [
    { sequence: 1, at: "2026-08-18T10:00:02Z", stage: "market_retrieval", detail: "loaded" },
    { sequence: 2, at: "2026-08-18T10:01:00Z", stage: "simulation", detail: "stepping" },
  ],
  result: {
    run_id: "canonical-9",
    strategy_label: "Trend Following",
    symbol: "EURUSD",
    timeframe: "H1",
    closed_trade_count: 24,
  },
};

describe("CanonicalRunMonitor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    streamEvents.current = [];
    runById.mockResolvedValue({ status: "success", data: RUN });
    cancelRun.mockResolvedValue({ status: "success", data: RUN });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads and displays canonical run state", async () => {
    render(<CanonicalRunMonitor runId="run-123" />);
    expect(await screen.findByText(/Job ID/i)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /cancel run/i })).toBeEnabled();
  });

  it("calls cancel on user action", async () => {
    render(<CanonicalRunMonitor runId="run-123" />);
    const button = await screen.findByRole("button", { name: /cancel run/i });
    button.click();
    await waitFor(() => expect(cancelRun).toHaveBeenCalledWith("run-123"));
  });

  it("renders ordered progress events and tracks the stream cursor", async () => {
    streamEvents.current = [
      { sequence: 1, payload: { stage: "market_retrieval", detail: "loaded" } },
      { sequence: 2, payload: { stage: "simulation", detail: "stepping" } },
    ];
    runById.mockResolvedValue({ status: "success", data: SUCCEEDED });
    runById.mockResolvedValueOnce({ status: "success", data: RUN });

    render(<CanonicalRunMonitor runId="run-123" />);

    const log = await screen.findByLabelText("run-log");
    await waitFor(() => {
      expect(log.textContent).toContain("market_retrieval: loaded");
      expect(log.textContent).toContain("simulation: stepping");
    });
    expect(
      log.textContent?.indexOf("market_retrieval"),
    ).toBeLessThan(log.textContent?.indexOf("simulation") ?? -1);

    await waitFor(() =>
      expect(screen.getByLabelText(/Stream connection state/i).textContent).toContain(
        "Last-Event-ID: 2",
      ),
    );
  });

  it("does not treat an early disconnect as a successful run", async () => {
    // The stream ends with no terminal frame and the authoritative read fails.
    runById.mockResolvedValueOnce({ status: "success", data: RUN });
    runById.mockResolvedValue({
      status: "error",
      error: { message: "run read unavailable" },
    });

    render(<CanonicalRunMonitor runId="run-123" />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain(
      "run stream ended without terminal run state",
    );
  });

  it("offers the canonical Analytics handoff only after success", async () => {
    runById.mockResolvedValue({ status: "success", data: SUCCEEDED });
    const onOpen = vi.fn();

    render(<CanonicalRunMonitor runId="run-123" onOpenAnalytics={onOpen} />);

    const button = await screen.findByRole("button", { name: /open analytics/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onOpen).toHaveBeenCalledWith("canonical-9");
  });
});
