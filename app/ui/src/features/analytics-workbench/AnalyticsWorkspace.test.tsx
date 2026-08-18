/**
 * Analytics Workbench shell tests (FEAT-UI-32 / P1-T04).
 *
 * Verifies that AnalyticsWorkspace renders all 7 analytical section tabs,
 * displays run metadata and evidence status, and handles tab switching.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { RunCatalogueEntry } from "@/clients";
import {
  AnalyticsNav,
  AnalyticsWorkspace,
} from "./index";

const SAMPLE_RUN_DETAIL: RunCatalogueEntry = {
  contract_version: "v1",
  schema_id: "api.run_catalogue_entry.v1",
  run_id: "run-anlt-100",
  principal_id: "user-1",
  origin_kind: "canonical_job",
  origin_id: "job-100",
  job_id: "job-100",
  batch_id: null,
  session_id: null,
  strategy_id: "ema_cross",
  strategy_version: "1.0.0",
  strategy_label: "EMA Trend Crossover",
  symbols: ["EURUSD", "GBPUSD"],
  timeframe: "1h",
  measurement_start: "2026-01-01T00:00:00Z",
  measurement_end: "2026-06-01T00:00:00Z",
  status: "completed",
  result_ref: "sim-res-100",
  report_id: "rep-100",
  report_ref: "anlt-rep-100",
  artifact_manifest_ref: "manifest-100",
  quality_status: "PASSED",
  evidence_class: "canonical",
  created_at: "2026-08-18T10:00:00Z",
  completed_at: "2026-08-18T10:05:00Z",
  name: "Baseline Multi-FX Run",
  alias: "multi-fx-base",
  description: "Canonical baseline backtest",
  tags: ["baseline", "fx"],
  run_reason: "Quarterly review",
  archive_state: "active",
};

describe("AnalyticsNav", () => {
  it("renders all 7 analytical tabs with role='tablist'", () => {
    const onTabChange = vi.fn();
    render(<AnalyticsNav activeTab="overview" onTabChange={onTabChange} />);

    expect(screen.getByRole("tablist", { name: /analytics sections/i })).toBeInTheDocument();
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(7);
    expect(tabs[0]).toHaveTextContent(/overview/i);
    expect(tabs[0]).toHaveAttribute("aria-selected", "true");
    expect(tabs[1]).toHaveTextContent(/returns & vami/i);
    expect(tabs[2]).toHaveTextContent(/drawdown & risk/i);
    expect(tabs[3]).toHaveTextContent(/trade analysis/i);
    expect(tabs[4]).toHaveTextContent(/grouped performance/i);
    expect(tabs[5]).toHaveTextContent(/benchmark & costs/i);
    expect(tabs[6]).toHaveTextContent(/artifacts & replay/i);
  });

  it("calls onTabChange on tab button click", () => {
    const onTabChange = vi.fn();
    render(<AnalyticsNav activeTab="overview" onTabChange={onTabChange} />);

    fireEvent.click(screen.getByRole("tab", { name: /returns & vami/i }));
    expect(onTabChange).toHaveBeenCalledWith("returns");

    fireEvent.click(screen.getByRole("tab", { name: /trade analysis/i }));
    expect(onTabChange).toHaveBeenCalledWith("trades");
  });
});

describe("AnalyticsWorkspace", () => {
  it("renders workspace shell with accessible heading and region", () => {
    render(<AnalyticsWorkspace runId="run-test-123" />);
    expect(screen.getByRole("region", { name: /analytics workspace/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: /run analysis: run-test-123/i })).toBeInTheDocument();
  });

  it("renders run metadata strip when runDetail is provided", () => {
    render(<AnalyticsWorkspace runDetail={SAMPLE_RUN_DETAIL} />);
    expect(screen.getByRole("heading", { level: 1, name: /baseline multi-fx run/i })).toBeInTheDocument();
    expect(screen.getByText(/ema trend crossover/i)).toBeInTheDocument();
    expect(screen.getByText(/eurusd, gbpusd/i)).toBeInTheDocument();
    expect(screen.getByText(/multi-fx-base/i)).toBeInTheDocument();
  });

  it("handles tab switching and renders tabpanel", () => {
    render(<AnalyticsWorkspace runDetail={SAMPLE_RUN_DETAIL} initialTab="overview" />);
    const returnsTab = screen.getByRole("tab", { name: /returns & vami/i });
    fireEvent.click(returnsTab);

    expect(returnsTab).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveAttribute("id", "analytics-panel-returns");
  });

  it("triggers onArchiveToggle when archive button is clicked", () => {
    const onArchiveToggle = vi.fn();
    render(
      <AnalyticsWorkspace
        runDetail={SAMPLE_RUN_DETAIL}
        onArchiveToggle={onArchiveToggle}
      />,
    );

    const archiveBtn = screen.getByRole("button", { name: /archive run/i });
    fireEvent.click(archiveBtn);
    expect(onArchiveToggle).toHaveBeenCalledWith(true);
  });

  it("renders custom children in tabpanel", () => {
    render(
      <AnalyticsWorkspace runId="run-123">
        <div data-testid="custom-analytics-child">Custom Metrics Matrix</div>
      </AnalyticsWorkspace>,
    );

    expect(screen.getByTestId("custom-analytics-child")).toBeInTheDocument();
    expect(screen.getByRole("tabpanel")).toContainElement(screen.getByTestId("custom-analytics-child"));
  });
});
