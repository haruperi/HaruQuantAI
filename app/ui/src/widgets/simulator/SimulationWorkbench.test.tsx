/**
 * Simulation Workbench shell tests (FEAT-UI-31 / P1-T02).
 *
 * Verifies that the workbench root renders required accessibility landmarks,
 * handles mode switching, surfaces engine evidence badges, and renders child panels.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  SimulationStatusBadge,
  SimulationWorkbench,
} from "./index";

describe("SimulationStatusBadge", () => {
  it("renders status badges with appropriate accessibility attributes", () => {
    const { rerender } = render(<SimulationStatusBadge status="running" />);
    expect(screen.getByRole("status")).toHaveTextContent(/running/i);

    rerender(<SimulationStatusBadge status="completed" />);
    expect(screen.getByRole("status")).toHaveTextContent(/completed/i);

    rerender(<SimulationStatusBadge status="failed" />);
    expect(screen.getByRole("status")).toHaveTextContent(/failed/i);

    rerender(<SimulationStatusBadge status="cancelled" />);
    expect(screen.getByRole("status")).toHaveTextContent(/cancelled/i);
  });

  it("renders evidence class pills", () => {
    const { rerender } = render(<SimulationStatusBadge evidenceClass="canonical" />);
    expect(screen.getByLabelText(/evidence: canonical/i)).toBeInTheDocument();

    rerender(<SimulationStatusBadge evidenceClass="practice" />);
    expect(screen.getByLabelText(/evidence: practice/i)).toBeInTheDocument();

    rerender(<SimulationStatusBadge evidenceClass="advisory" />);
    expect(screen.getByLabelText(/evidence: advisory/i)).toBeInTheDocument();

    rerender(<SimulationStatusBadge evidenceClass="playback" />);
    expect(screen.getByLabelText(/evidence: playback/i)).toBeInTheDocument();

    rerender(<SimulationStatusBadge evidenceClass="fast_research" />);
    expect(screen.getByLabelText(/evidence: fast research/i)).toBeInTheDocument();
  });

  it("renders archived badge when archiveState is archived", () => {
    render(<SimulationStatusBadge archiveState="archived" />);
    expect(screen.getByLabelText(/archived/i)).toBeInTheDocument();
  });
});

describe("SimulationWorkbench", () => {
  it("renders root shell with accessible landmark and heading", () => {
    render(<SimulationWorkbench />);
    const region = screen.getByRole("region", { name: /simulation workbench/i });
    expect(region).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: /simulation workbench/i })).toBeInTheDocument();
  });

  it("renders 4 mode tabs with accessible tablist", () => {
    render(<SimulationWorkbench initialMode="canonical" />);
    const tablist = screen.getByRole("tablist", { name: /simulation modes/i });
    expect(tablist).toBeInTheDocument();

    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(4);
    expect(tabs[0]).toHaveTextContent(/canonical run/i);
    expect(tabs[0]).toHaveAttribute("aria-selected", "true");
    expect(tabs[1]).toHaveTextContent(/live practice/i);
    expect(tabs[1]).toHaveAttribute("aria-selected", "false");
  });

  it("switches modes on tab click and fires onModeChange", () => {
    const onModeChange = vi.fn();
    render(<SimulationWorkbench initialMode="canonical" onModeChange={onModeChange} />);

    const practiceTab = screen.getByRole("tab", { name: /live practice/i });
    fireEvent.click(practiceTab);

    expect(practiceTab).toHaveAttribute("aria-selected", "true");
    expect(onModeChange).toHaveBeenCalledWith("practice");

    const batchTab = screen.getByRole("tab", { name: /batch grid/i });
    fireEvent.click(batchTab);
    expect(batchTab).toHaveAttribute("aria-selected", "true");
    expect(onModeChange).toHaveBeenCalledWith("batch");
  });

  it("renders custom children inside tabpanel", () => {
    render(
      <SimulationWorkbench initialMode="canonical">
        <div data-testid="custom-child">Custom Simulation Content</div>
      </SimulationWorkbench>,
    );

    expect(screen.getByTestId("custom-child")).toBeInTheDocument();
    expect(screen.getByRole("tabpanel")).toContainElement(screen.getByTestId("custom-child"));
  });

  it("renders active run and session IDs when provided", () => {
    render(
      <SimulationWorkbench
        initialMode="practice"
        initialRunId="run-test-123"
        initialSessionId="sess-test-456"
      />,
    );

    expect(screen.getByText(/active run: run-test-123/i)).toBeInTheDocument();
    expect(screen.getByText(/active session: sess-test-456/i)).toBeInTheDocument();
  });
});
