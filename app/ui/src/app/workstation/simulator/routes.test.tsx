/**
 * Simulator workspace route tests (FEAT-UI-31 / P1-T03).
 *
 * Verifies that the simulator route components parse route segments,
 * select appropriate initial modes, pass down active identifiers, and render the workbench.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SimulatorPage from "./page";
import NewSimulationPage from "./new/page";
import SimulatorSegmentsPage from "./[...segments]/page";

vi.mock("@/app/protected-layout", () => ({
  ProtectedLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-layout">{children}</div>
  ),
}));

vi.mock("@/features/simulation-workbench", () => ({
  SimulationHome: (props: {
    initialMode?: string;
    initialRunId?: string;
    initialSessionId?: string;
    initialBatchId?: string;
  }) => {
    const mode = props.initialMode ?? "canonical";
    return (
      <div data-testid="simulation-home">
        <span>Mode: {mode}</span>
        {props.initialRunId ? <span>Run: {props.initialRunId}</span> : null}
        {props.initialSessionId ? (
          <span>Session: {props.initialSessionId}</span>
        ) : null}
        {props.initialBatchId ? <span>Batch: {props.initialBatchId}</span> : null}
      </div>
    );
  },
  SimulationPlaybackWorkspace: (props: {
    runId: string;
    ticket?: string;
    returnHref?: string;
  }) => (
    <div data-testid="simulation-playback">
      <span>Replay run: {props.runId}</span>
      {props.ticket ? <span>Ticket: {props.ticket}</span> : null}
      {props.returnHref ? <span>Return: {props.returnHref}</span> : null}
    </div>
  ),
}));

let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

describe("Simulator Routes", () => {
  it("SimulatorPage renders canonical SimulationHome", () => {
    render(<SimulatorPage />);
    expect(screen.getByTestId("protected-layout")).toBeInTheDocument();
    expect(screen.getByText(/mode: canonical/i)).toBeInTheDocument();
  });

  it("NewSimulationPage renders canonical SimulationHome", () => {
    render(<NewSimulationPage />);
    expect(screen.getByText(/mode: canonical/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles practice mode without sessionId", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["practice"] }} />);
    expect(screen.getByText(/mode:\s*practice/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles practice mode with sessionId", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["practice", "sess-abc-123"] }} />);
    expect(screen.getByText(/mode:\s*practice/i)).toBeInTheDocument();
    expect(screen.getByText(/session: sess-abc-123/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles batch mode with batchId", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["batch", "batch-grid-999"] }} />);
    expect(screen.getByText(/mode: batch/i)).toBeInTheDocument();
    expect(screen.getByText(/batch: batch-grid-999/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles history mode", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["history"] }} />);
    expect(screen.getByText(/mode:\s*history/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles runs/[runId] mode", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["runs", "run-canon-456"] }} />);
    expect(screen.getByText(/mode: canonical/i)).toBeInTheDocument();
    expect(screen.getByText(/run: run-canon-456/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage renders immutable playback with its return context", () => {
    mockSearchParams = new URLSearchParams(
      "ticket=1001&return=%2Fworkstation%2Fanalytics%2Fcanonical-1%2Ftrades%2F1001",
    );
    render(
      <SimulatorSegmentsPage params={{ segments: ["replay", "canonical-1"] }} />,
    );
    expect(screen.getByTestId("simulation-playback")).toBeInTheDocument();
    expect(screen.getByText("Replay run: canonical-1")).toBeInTheDocument();
    expect(screen.getByText("Ticket: 1001")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Return: /workstation/analytics/canonical-1/trades/1001",
      ),
    ).toBeInTheDocument();
  });
});
