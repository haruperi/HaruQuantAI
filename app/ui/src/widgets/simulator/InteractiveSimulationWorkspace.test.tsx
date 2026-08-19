/**
 * Interactive workspace tests (FEAT-UI-31, P4-T03).
 *
 * Covers the four pacing rules: pause stops the scheduler, losing visibility
 * pauses, reconnecting reads authoritative state first, and a failed advance
 * never moves the cursor.
 */

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { getLiveSession, getViewport, stepLiveSession, seekLiveSession } =
  vi.hoisted(() => ({
    getLiveSession: vi.fn(),
    getViewport: vi.fn(),
    stepLiveSession: vi.fn(),
    seekLiveSession: vi.fn(),
  }));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    simulationWorkbench: {
      getLiveSession,
      getViewport,
      stepLiveSession,
      seekLiveSession,
    },
  },
}));

import {
  InteractiveSimulationWorkspace,
  PLAY_INTERVAL_MS,
  VIEWPORT_ROWS,
} from "./InteractiveSimulationWorkspace";

/** One authoritative session projection at a given cursor. */
function sessionAt(cursor: number, overrides: Record<string, unknown> = {}) {
  return {
    contract_version: "v1",
    schema_id: "api.live_session_projection.v1",
    session_id: "session-1",
    run_id: "advisory-1",
    mode: "practice",
    evidence_class: "practice",
    cursor,
    timestamp: `2025-03-04T0${cursor}:00:00Z`,
    tick_count: 100,
    completed: false,
    dataset: { dataset_id: "ds-1", revision: "rev-1", content_hash: "h" },
    positions: [],
    orders: [],
    pending_intent_count: 0,
    exposure_blocked: false,
    state_hash: "hash",
    state_freshness: "fresh",
    permitted_actions: ["read", "step", "seek", "command"],
    ...overrides,
  };
}

const VIEWPORT = {
  session_id: "session-1",
  cursor: 0,
  timestamp: "2025-03-04T00:00:00Z",
  before: VIEWPORT_ROWS,
  after: 0,
  rows: [],
};

describe("InteractiveSimulationWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    getLiveSession.mockResolvedValue({ status: "success", data: sessionAt(0) });
    getViewport.mockResolvedValue({ status: "success", data: VIEWPORT });
    stepLiveSession.mockResolvedValue({
      status: "success",
      data: sessionAt(1),
    });
    seekLiveSession.mockResolvedValue({
      status: "success",
      data: sessionAt(100, { completed: true }),
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("reads authoritative state and the backwards-only viewport on mount", async () => {
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await waitFor(() => expect(getLiveSession).toHaveBeenCalledWith("session-1"));
    expect(getViewport).toHaveBeenCalledWith("session-1", {
      before: VIEWPORT_ROWS,
    });
    expect(await screen.findByText("0 of 100")).toBeInTheDocument();
  });

  it("shows the server cursor after a step, never a predicted one", async () => {
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("0 of 100");

    fireEvent.click(screen.getByRole("button", { name: "Step 10" }));
    await waitFor(() =>
      expect(stepLiveSession).toHaveBeenCalledWith("session-1", { ticks: 10 }),
    );
    expect(await screen.findByText("1 of 100")).toBeInTheDocument();
  });

  it("stops the scheduler when playback is paused", async () => {
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("0 of 100");

    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await act(async () => {
      vi.advanceTimersByTime(PLAY_INTERVAL_MS);
    });
    await waitFor(() => expect(stepLiveSession).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    await act(async () => {
      vi.advanceTimersByTime(PLAY_INTERVAL_MS * 5);
    });
    expect(stepLiveSession).toHaveBeenCalledTimes(1);
  });

  it("pauses when the page loses visibility", async () => {
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("0 of 100");
    fireEvent.click(screen.getByRole("button", { name: "Play" }));

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => "hidden",
    });
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    expect(
      await screen.findByRole("button", { name: "Play" }),
    ).toBeInTheDocument();
    await act(async () => {
      vi.advanceTimersByTime(PLAY_INTERVAL_MS * 3);
    });
    expect(stepLiveSession).not.toHaveBeenCalled();

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => "visible",
    });
  });

  it("reads authoritative state before resuming after reconnecting", async () => {
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("0 of 100");
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    getLiveSession.mockClear();

    getLiveSession.mockResolvedValue({
      status: "success",
      data: sessionAt(42),
    });
    await act(async () => {
      window.dispatchEvent(new Event("online"));
    });

    await waitFor(() => expect(getLiveSession).toHaveBeenCalledWith("session-1"));
    expect(await screen.findByText("42 of 100")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Play" }),
    ).toBeInTheDocument();
  });

  it("never advances the cursor when an advance fails", async () => {
    stepLiveSession.mockResolvedValue({
      status: "error",
      error: { message: "SIMULATION_SESSION_FINALIZED" },
    });
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("0 of 100");

    fireEvent.click(screen.getByRole("button", { name: "Step 1" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "SIMULATION_SESSION_FINALIZED",
    );
    expect(screen.getByText("0 of 100")).toBeInTheDocument();
  });

  it("stops playback when an advance fails mid-run", async () => {
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("0 of 100");
    fireEvent.click(screen.getByRole("button", { name: "Play" }));

    stepLiveSession.mockResolvedValue({
      status: "error",
      error: { message: "engine unavailable" },
    });
    await act(async () => {
      vi.advanceTimersByTime(PLAY_INTERVAL_MS);
    });

    expect(await screen.findByRole("button", { name: "Play" })).toBeInTheDocument();
    const attempts = stepLiveSession.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(PLAY_INTERVAL_MS * 3);
    });
    expect(stepLiveSession).toHaveBeenCalledTimes(attempts);
  });

  it("blocks advancing while exposure is blocked", async () => {
    getLiveSession.mockResolvedValue({
      status: "success",
      data: sessionAt(5, { exposure_blocked: true }),
    });
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("5 of 100");

    expect(screen.getByRole("button", { name: "Play" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Step 1" })).toBeDisabled();
    expect(
      screen.getByText(/Exposure is blocked until this session is explicitly rearmed\./),
    ).toBeInTheDocument();
  });

  it("seeks forward to the authoritative end cursor", async () => {
    render(<InteractiveSimulationWorkspace sessionId="session-1" />);
    await screen.findByText("0 of 100");

    fireEvent.click(screen.getByRole("button", { name: "Seek to end" }));
    await waitFor(() =>
      expect(seekLiveSession).toHaveBeenCalledWith("session-1", {
        target_cursor: 100,
      }),
    );
    expect(await screen.findByText("100 of 100")).toBeInTheDocument();
  });
});
