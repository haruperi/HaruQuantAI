/**
 * Run catalogue panel tests (FEAT-UI-31).
 *
 * Covers the loading, empty, error, and populated states of the historical
 * catalogue that replaced the staged-rollout placeholder, plus its paging
 * controls and hand-off links into the Analytics workspace.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { listRuns } = vi.hoisted(() => ({ listRuns: vi.fn() }));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: { analyticsWorkbench: { listRuns } },
}));

import { CATALOGUE_PAGE_SIZE, RunCataloguePanel } from "./RunCataloguePanel";

const ENTRY = {
  run_id: "canonical-1",
  principal_id: "user-1",
  origin_kind: "canonical_job",
  origin_id: "job-1",
  job_id: "job-1",
  batch_id: null,
  session_id: null,
  strategy_id: "trend",
  strategy_version: "1.2.0",
  strategy_label: "Trend Following",
  symbols: ["EURUSD"],
  timeframe: "H1",
  measurement_start: "2025-01-01T00:00:00Z",
  measurement_end: "2025-12-31T00:00:00Z",
  status: "completed",
  result_ref: "result-1",
  report_id: "report-1",
  report_ref: "report-ref-1",
  artifact_manifest_ref: "manifest-1",
  quality_status: "acceptable",
  evidence_class: "canonical",
  created_at: "2026-01-02T00:00:00Z",
  completed_at: "2026-01-02T00:10:00Z",
  name: "Baseline",
  alias: null,
  description: null,
  tags: [],
  run_reason: null,
  archive_state: "active",
};

describe("RunCataloguePanel", () => {
  beforeEach(() => {
    listRuns.mockReset();
  });

  it("renders recorded runs with an Analytics hand-off link", async () => {
    listRuns.mockResolvedValue({ status: "success", data: { runs: [ENTRY] } });

    render(<RunCataloguePanel />);

    await waitFor(() => expect(screen.getByText("canonical-1")).toBeInTheDocument());
    expect(screen.getByText("Trend Following")).toBeInTheDocument();
    expect(screen.getByText("canonical_job")).toBeInTheDocument();
    expect(screen.getByText("2025-01-01 → 2025-12-31")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open in Analytics" })).toHaveAttribute(
      "href",
      "/workstation/analytics/canonical-1/overview",
    );
  });

  it("requests the bounded page size and pages forward on demand", async () => {
    listRuns.mockResolvedValue({
      status: "success",
      data: {
        runs: Array.from({ length: CATALOGUE_PAGE_SIZE }, (_unused, index) => ({
          ...ENTRY,
          run_id: `canonical-${index}`,
        })),
      },
    });

    render(<RunCataloguePanel />);

    await waitFor(() =>
      expect(listRuns).toHaveBeenCalledWith({ page: 1, page_size: CATALOGUE_PAGE_SIZE }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() =>
      expect(listRuns).toHaveBeenCalledWith({ page: 2, page_size: CATALOGUE_PAGE_SIZE }),
    );
  });

  it("states plainly when no runs have been recorded", async () => {
    listRuns.mockResolvedValue({ status: "success", data: { runs: [] } });

    render(<RunCataloguePanel />);

    await waitFor(() =>
      expect(screen.getByText("No runs have been recorded yet.")).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("surfaces a server refusal instead of an empty catalogue", async () => {
    listRuns.mockResolvedValue({
      status: "error",
      error: { message: "ANALYTICS_WORKBENCH_RUNTIME_UNAVAILABLE" },
    });

    render(<RunCataloguePanel />);

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "ANALYTICS_WORKBENCH_RUNTIME_UNAVAILABLE",
      ),
    );
  });

  it("surfaces a thrown transport failure", async () => {
    listRuns.mockRejectedValue(new Error("network down"));

    render(<RunCataloguePanel />);

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("network down"),
    );
  });
});
