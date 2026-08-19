/**
 * SimulationHome routing and panel dispatch tests (FEAT-UI-31).
 */

import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const { builderProps } = vi.hoisted(() => ({
  builderProps: { current: null as Record<string, unknown> | null },
}));

vi.mock("./SimulationRunBuilder", () => ({
  SimulationRunBuilder: (props: Record<string, unknown>) => {
    builderProps.current = props;
    return <div data-testid="run-builder" data-mode={String(props.initialMode)} />;
  },
}));
vi.mock("./CanonicalRunMonitor", () => ({
  CanonicalRunMonitor: ({ runId }: { runId: string }) => (
    <div data-testid="canonical-monitor" data-run-id={runId} />
  ),
}));
vi.mock("./BatchRunMonitor", () => ({
  BatchRunMonitor: ({ batchId }: { batchId: string }) => (
    <div data-testid="batch-monitor" data-batch-id={batchId} />
  ),
}));

import { SimulationHome } from "./SimulationHome";

describe("SimulationHome", () => {
  it("renders builder for canonical mode without runId", () => {
    render(<SimulationHome initialMode="canonical" />);
    expect(screen.getByTestId("run-builder")).toHaveAttribute(
      "data-mode",
      "canonical_backtest",
    );
  });

  it("renders canonical monitor for canonical mode with runId", () => {
    render(<SimulationHome initialMode="canonical" initialRunId="run-abc" />);
    expect(screen.getByTestId("canonical-monitor")).toBeInTheDocument();
  });

  it("renders the batch builder for batch mode without a batch identity", () => {
    render(<SimulationHome initialMode="batch" />);
    expect(screen.getByTestId("run-builder")).toHaveAttribute(
      "data-mode",
      "batch",
    );
  });

  it("renders batch monitor for batch mode with batchId", () => {
    render(<SimulationHome initialMode="batch" initialBatchId="batch-999" />);
    expect(screen.getByTestId("batch-monitor")).toBeInTheDocument();
  });

  it("renders placeholders for empty practice and history modes", () => {
    const first = render(<SimulationHome initialMode="practice" />);
    expect(screen.getByRole("heading", { name: /^Live practice$/i })).toBeInTheDocument();
    expect(
      screen.getByText("No practice session identifier was provided."),
    ).toBeInTheDocument();
    first.unmount();

    render(<SimulationHome initialMode="history" />);
    expect(screen.getByRole("heading", { name: /run catalogue/i })).toBeInTheDocument();
  });

  it("hands a submitted run off to the canonical monitor", () => {
    render(<SimulationHome initialMode="canonical" />);
    const onSubmitted = builderProps.current?.onSubmitted as (
      submission: { kind: "run"; runId: string },
    ) => void;

    act(() => onSubmitted({ kind: "run", runId: "run-from-builder" }));

    expect(screen.getByTestId("canonical-monitor")).toHaveAttribute(
      "data-run-id",
      "run-from-builder",
    );
  });

  it("hands a submitted batch off to the batch monitor", () => {
    render(<SimulationHome initialMode="batch" />);
    const onSubmitted = builderProps.current?.onSubmitted as (
      submission: { kind: "batch"; batchId: string },
    ) => void;

    act(() => onSubmitted({ kind: "batch", batchId: "batch-from-builder" }));

    expect(screen.getByTestId("batch-monitor")).toHaveAttribute(
      "data-batch-id",
      "batch-from-builder",
    );
  });
});
