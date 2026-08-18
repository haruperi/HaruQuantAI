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

vi.mock("@/features/simulator", () => ({
  SimulatorWidget: () => <div data-testid="simulator-widget">Simulator Widget Mock</div>,
}));

describe("Simulator Routes", () => {
  it("SimulatorPage renders Workbench in canonical mode with SimulatorWidget", () => {
    render(<SimulatorPage />);
    expect(screen.getByTestId("protected-layout")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /simulation workbench/i })).toBeInTheDocument();
    expect(screen.getByTestId("simulator-widget")).toBeInTheDocument();
  });

  it("NewSimulationPage renders Workbench with new run builder", () => {
    render(<NewSimulationPage />);
    expect(screen.getByRole("region", { name: /simulation workbench/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /canonical run/i })).toHaveAttribute("aria-selected", "true");
  });

  it("SimulatorSegmentsPage handles practice mode without sessionId", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["practice"] }} />);
    expect(screen.getByRole("tab", { name: /live practice/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("heading", { name: /live practice/i })).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles practice mode with sessionId", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["practice", "sess-abc-123"] }} />);
    expect(screen.getByRole("tab", { name: /live practice/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/active session: sess-abc-123/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles batch mode with batchId", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["batch", "batch-grid-999"] }} />);
    expect(screen.getByRole("tab", { name: /batch grid/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/active batch: batch-grid-999/i)).toBeInTheDocument();
  });

  it("SimulatorSegmentsPage handles history mode", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["history"] }} />);
    expect(screen.getByRole("tab", { name: /run catalogue/i })).toHaveAttribute("aria-selected", "true");
  });

  it("SimulatorSegmentsPage handles runs/[runId] mode", () => {
    render(<SimulatorSegmentsPage params={{ segments: ["runs", "run-canon-456"] }} />);
    expect(screen.getByRole("tab", { name: /canonical run/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/active run: run-canon-456/i)).toBeInTheDocument();
  });
});
