/**
 * Run comparison tests (FEAT-UI-32, P6-T03).
 *
 * The store holds only the selection and presentation choice, and the rendered
 * comparison is always the owner's: no difference is computed in the browser.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { listRuns, compareRuns } = vi.hoisted(() => ({
  listRuns: vi.fn(),
  compareRuns: vi.fn(),
}));

vi.mock("@/clients", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    ApiClientError: class extends Error {},
    apiClients: { analyticsWorkbench: { listRuns, compareRuns } },
  };
});

import { AnalyticsComparison } from "./AnalyticsComparison";
import { useAnalyticsWorkbenchStore } from "./analytics-store";
import {
  MAX_COMPARISON_RUNS,
  isComparable,
  toComparisonRows,
  toggleSelection,
} from "./analytics-selectors";

/** One catalogue row. */
function entry(runId: string) {
  return {
    run_id: runId,
    principal_id: "user-1",
    origin_kind: "canonical_job",
    origin_id: "job-1",
    strategy_id: "trend",
    symbols: ["EURUSD"],
    timeframe: "H1",
    measurement_start: "2025-01-01T00:00:00Z",
    measurement_end: "2025-12-31T00:00:00Z",
    status: "completed",
    evidence_class: "canonical",
    created_at: "2026-01-02T00:00:00Z",
    tags: [],
    archive_state: "active",
    name: null,
  };
}

describe("analytics-selectors", () => {
  it("bounds the selection to the comparison maximum", () => {
    let selection: string[] = [];
    for (let index = 0; index < MAX_COMPARISON_RUNS + 3; index += 1) {
      selection = toggleSelection(selection, `run-${index}`);
    }
    expect(selection).toHaveLength(MAX_COMPARISON_RUNS);
  });

  it("toggles a run out of the selection", () => {
    expect(toggleSelection(["a", "b"], "a")).toEqual(["b"]);
  });

  it("requires at least two runs to compare", () => {
    expect(isComparable(["a"])).toBe(false);
    expect(isComparable(["a", "b"])).toBe(true);
  });

  it("projects owner rows without combining them", () => {
    const rows = toComparisonRows({
      contract_version: "v1",
      schema_id: "analytics.comparison_evidence.v1",
      metric: "summary",
      runs: [
        {
          run_id: "a",
          label: "Net PnL",
          value: "100.00",
          unit: "USD",
          source_context: "all",
        },
        { run_id: "b", label: "Net PnL", value: null, unit: "USD" },
      ],
    });
    expect(rows).toEqual([
      {
        runId: "a",
        label: "Net PnL",
        value: "100.00",
        unit: "USD",
        context: "all",
      },
      {
        runId: "b",
        label: "Net PnL",
        value: null,
        unit: "USD",
        context: "all",
      },
    ]);
  });
});

describe("AnalyticsComparison", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAnalyticsWorkbenchStore.getState().clearSelection();
    listRuns.mockResolvedValue({
      status: "success",
      data: { runs: [entry("run-a"), entry("run-b")] },
    });
    compareRuns.mockResolvedValue({
      status: "success",
      data: {
        contract_version: "v1",
        schema_id: "analytics.comparison_evidence.v1",
        metric: "summary",
        runs: [
          {
            run_id: "run-a",
            label: "Net PnL",
            value: "100.00",
            unit: "USD",
            source_context: "all",
          },
          {
            run_id: "run-b",
            label: "Net PnL",
            value: "250.00",
            unit: "USD",
            source_context: "all",
          },
        ],
      },
    });
  });

  it("keeps the compare action disabled below two selected runs", async () => {
    render(<AnalyticsComparison />);
    await screen.findByText(/run-a/);
    expect(
      screen.getByRole("button", { name: /compare selected runs/i }),
    ).toBeDisabled();
  });

  it("delegates the comparison to Analytics with the selected metric", async () => {
    render(<AnalyticsComparison initialRunIds={["run-a", "run-b"]} />);
    await screen.findByText(/run-a/);

    fireEvent.change(screen.getByLabelText("Metric group"), {
      target: { value: "risk" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /compare selected runs/i }),
    );

    await waitFor(() =>
      expect(compareRuns).toHaveBeenCalledWith({
        run_ids: ["run-a", "run-b"],
        metric: "risk",
      }),
    );
  });

  it("renders owner values verbatim and computes no difference", async () => {
    render(<AnalyticsComparison initialRunIds={["run-a", "run-b"]} />);
    await screen.findByText(/run-a/);
    fireEvent.click(
      screen.getByRole("button", { name: /compare selected runs/i }),
    );

    const table = await screen.findByLabelText("Comparison evidence");
    expect(within(table).getByText("100.00")).toBeInTheDocument();
    expect(within(table).getByText("250.00")).toBeInTheDocument();
    expect(table.textContent).not.toContain("150");
  });

  it("marks a value the owner omitted as unavailable", async () => {
    compareRuns.mockResolvedValue({
      status: "success",
      data: {
        contract_version: "v1",
        schema_id: "analytics.comparison_evidence.v1",
        metric: "summary",
        runs: [
          { run_id: "run-a", label: "Net PnL", value: "100.00", unit: "USD" },
          { run_id: "run-b", label: "Net PnL", value: null, unit: "USD" },
        ],
      },
    });
    render(<AnalyticsComparison initialRunIds={["run-a", "run-b"]} />);
    await screen.findByText(/run-a/);
    fireEvent.click(
      screen.getByRole("button", { name: /compare selected runs/i }),
    );

    const table = await screen.findByLabelText("Comparison evidence");
    expect(within(table).getByText("Unavailable")).toBeInTheDocument();
  });

  it("surfaces a comparison failure instead of a partial table", async () => {
    compareRuns.mockResolvedValue({
      status: "error",
      error: { message: "runs are not comparable" },
    });
    render(<AnalyticsComparison initialRunIds={["run-a", "run-b"]} />);
    await screen.findByText(/run-a/);
    fireEvent.click(
      screen.getByRole("button", { name: /compare selected runs/i }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "runs are not comparable",
    );
    expect(screen.queryByLabelText("Comparison evidence")).toBeNull();
  });
});
