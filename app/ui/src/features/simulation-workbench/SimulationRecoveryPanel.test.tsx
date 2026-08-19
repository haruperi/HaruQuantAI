/**
 * Recovery and finalization tests (FEAT-UI-31, P4-T05).
 *
 * Restore, verify, and rearm stay three separate steps, a failed integrity
 * check disables rearm, and finalization is presented as advisory sealing
 * rather than as promotion to a canonical run.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  restoreLiveSession,
  rearmLiveSession,
  finalizeLiveSession,
  reproduceLiveSession,
} = vi.hoisted(() => ({
  restoreLiveSession: vi.fn(),
  rearmLiveSession: vi.fn(),
  finalizeLiveSession: vi.fn(),
  reproduceLiveSession: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    simulationWorkbench: {
      restoreLiveSession,
      rearmLiveSession,
      finalizeLiveSession,
      reproduceLiveSession,
    },
  },
}));

import type { LiveSessionProjection } from "@/clients";
import { SimulationRecoveryPanel } from "./SimulationRecoveryPanel";
import {
  SimulationFinalizeDialog,
  FINALIZE_ADVISORY_NOTICE,
} from "./SimulationFinalizeDialog";

/** One authoritative session projection. */
function session(overrides: Record<string, unknown> = {}) {
  return {
    contract_version: "v1",
    schema_id: "api.live_session_projection.v1",
    session_id: "session-1",
    run_id: "advisory-1",
    mode: "practice",
    evidence_class: "practice",
    cursor: 12,
    timestamp: "2025-03-04T08:00:00Z",
    tick_count: 100,
    completed: false,
    positions: [],
    orders: [],
    pending_intent_count: 0,
    exposure_blocked: false,
    state_hash: "hash",
    state_freshness: "fresh",
    permitted_actions: ["read"],
    ...overrides,
  } as unknown as LiveSessionProjection;
}

/** One reconstructed session awaiting explicit rearm. */
function restored(integrity: string) {
  return session({
    exposure_blocked: true,
    recovery: {
      status: "recovery_blocked",
      persisted_state_hash: "0xstate",
      integrity_status: integrity,
      recovery_generation: 2,
      recovery_run_id: "recovery-1",
      last_checkpoint_at: "2025-03-04T07:59:00Z",
    },
  });
}

describe("SimulationRecoveryPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    restoreLiveSession.mockResolvedValue({
      status: "success",
      data: restored("verified"),
    });
    rearmLiveSession.mockResolvedValue({
      status: "success",
      data: session(),
    });
  });

  it("presents restore, verify, and rearm as separate steps", () => {
    render(
      <SimulationRecoveryPanel sessionId="session-1" session={session()} />,
    );
    expect(
      screen.getByText(/Restore the persisted session from its durable checkpoint\./),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Verify the reconstructed state against its recorded digest\./),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Rearm explicitly before the session may act on the market again\./),
    ).toBeInTheDocument();
  });

  it("leaves rearm disabled until a session has been restored", () => {
    render(
      <SimulationRecoveryPanel sessionId="session-1" session={session()} />,
    );
    expect(screen.getByRole("button", { name: /rearm session/i })).toBeDisabled();
  });

  it("does not rearm as a side effect of restoring", async () => {
    const onSessionChanged = vi.fn();
    render(
      <SimulationRecoveryPanel
        sessionId="session-1"
        session={session()}
        onSessionChanged={onSessionChanged}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /restore session/i }));

    await waitFor(() =>
      expect(restoreLiveSession).toHaveBeenCalledWith("session-1"),
    );
    expect(rearmLiveSession).not.toHaveBeenCalled();
    expect(onSessionChanged).toHaveBeenCalledTimes(1);
  });

  it("enables rearm only once integrity verified", () => {
    render(
      <SimulationRecoveryPanel
        sessionId="session-1"
        session={restored("verified")}
      />,
    );
    expect(screen.getByRole("button", { name: /rearm session/i })).toBeEnabled();
  });

  it("disables rearm when integrity verification failed", () => {
    render(
      <SimulationRecoveryPanel
        sessionId="session-1"
        session={restored("mismatch")}
      />,
    );
    expect(screen.getByRole("button", { name: /rearm session/i })).toBeDisabled();
    expect(
      screen.getByText(/Integrity verification did not succeed/),
    ).toBeInTheDocument();
  });

  it("requires explicit approval when rearming", async () => {
    render(
      <SimulationRecoveryPanel
        sessionId="session-1"
        session={restored("verified")}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /rearm session/i }));
    await waitFor(() =>
      expect(rearmLiveSession).toHaveBeenCalledWith("session-1", true),
    );
  });

  it("renders the recorded recovery evidence", () => {
    render(
      <SimulationRecoveryPanel
        sessionId="session-1"
        session={restored("verified")}
      />,
    );
    expect(screen.getByText("0xstate")).toBeInTheDocument();
    expect(screen.getByText("recovery-1")).toBeInTheDocument();
    expect(screen.getByText("blocked")).toBeInTheDocument();
  });

  it("surfaces a restore failure without changing state", async () => {
    restoreLiveSession.mockResolvedValue({
      status: "error",
      error: { message: "checkpoint incompatible" },
    });
    const onSessionChanged = vi.fn();
    render(
      <SimulationRecoveryPanel
        sessionId="session-1"
        session={session()}
        onSessionChanged={onSessionChanged}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /restore session/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "checkpoint incompatible",
    );
    expect(onSessionChanged).not.toHaveBeenCalled();
  });
});

describe("SimulationFinalizeDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    finalizeLiveSession.mockResolvedValue({
      status: "success",
      data: session({ finalized: true }),
    });
    reproduceLiveSession.mockResolvedValue({
      status: "success",
      data: { job_id: "canonical-77" },
    });
  });

  it("states that finalization stays advisory", () => {
    render(
      <SimulationFinalizeDialog sessionId="session-1" session={session()} />,
    );
    expect(screen.getByText(FINALIZE_ADVISORY_NOTICE)).toBeInTheDocument();
  });

  it("requires confirmation before sealing", async () => {
    render(
      <SimulationFinalizeDialog sessionId="session-1" session={session()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^finalize session$/i }));
    expect(finalizeLiveSession).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /confirm finalize/i }));
    await waitFor(() =>
      expect(finalizeLiveSession).toHaveBeenCalledWith("session-1"),
    );
  });

  it("offers reproduction only after the session is sealed", () => {
    render(
      <SimulationFinalizeDialog
        sessionId="session-1"
        session={session({ finalized: true })}
      />,
    );
    expect(
      screen.getByRole("button", { name: /reproduce as canonical run/i }),
    ).toBeEnabled();
    expect(screen.queryByRole("button", { name: /^finalize session$/i })).toBeNull();
  });

  it("reports the distinct canonical job reproduction created", async () => {
    const onReproduced = vi.fn();
    render(
      <SimulationFinalizeDialog
        sessionId="session-1"
        session={session({ finalized: true })}
        onReproduced={onReproduced}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: /reproduce as canonical run/i }),
    );

    await waitFor(() =>
      expect(reproduceLiveSession).toHaveBeenCalledWith("session-1"),
    );
    expect(await screen.findByText(/canonical-77/)).toBeInTheDocument();
    expect(onReproduced).toHaveBeenCalledWith({ job_id: "canonical-77" });
  });

  it("surfaces a finalization failure without claiming the seal succeeded", async () => {
    finalizeLiveSession.mockResolvedValue({
      status: "error",
      error: { message: "SIMULATION_SESSION_FINALIZED" },
    });
    render(
      <SimulationFinalizeDialog sessionId="session-1" session={session()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^finalize session$/i }));
    fireEvent.click(screen.getByRole("button", { name: /confirm finalize/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "SIMULATION_SESSION_FINALIZED",
    );
    expect(
      screen.queryByText("This session is finalized and sealed."),
    ).toBeNull();
  });
});
