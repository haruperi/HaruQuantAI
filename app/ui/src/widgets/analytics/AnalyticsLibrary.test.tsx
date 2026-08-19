/**
 * Analytics library and overview tests (FEAT-UI-32, P3-T01).
 *
 * Covers server pagination, archive as a metadata-only transition, unavailable
 * metrics, units, quality flags, caveats, and long/short source contexts.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { listRuns, archiveRun, getRun, getWorkbenchPayload } = vi.hoisted(() => ({
  listRuns: vi.fn(),
  archiveRun: vi.fn(),
  getRun: vi.fn(),
  getWorkbenchPayload: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    analyticsWorkbench: { listRuns, archiveRun, getRun, getWorkbenchPayload },
  },
}));

import { AnalyticsLibrary, LIBRARY_PAGE_SIZE } from "./AnalyticsLibrary";
import { OverviewPanel } from "./OverviewPanel";

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
  tags: ["baseline"],
  run_reason: null,
  archive_state: "active",
};

/** One section fixture in the owner projection shape. */
function section(overrides: Record<string, unknown> = {}) {
  return {
    key: "summary",
    status: "completed",
    unit: null,
    source_context: "all",
    sample_count: 2,
    reason: null,
    truncated: false,
    total_count: 2,
    items: [],
    ...overrides,
  };
}

const PAYLOAD = {
  contract_version: "v1",
  schema_id: "analytics.workbench_payload.v1",
  payload_id: "payload-1",
  report_id: "report-1",
  generated_at: "2026-01-02T00:11:00Z",
  summary: section({
    items: [
      { key: "net_pnl", label: "Net PnL", value: "1234.50", unit: "USD" },
      { key: "sharpe_ratio", label: "Sharpe Ratio", value: "1.12", unit: null },
      {
        key: "win_rate",
        label: "Win Rate",
        value: "0.55",
        unit: "ratio",
        source_context: "long",
      },
    ],
  }),
  equity_curve: section({ key: "equity_curve", source_context: "all" }),
  drawdown_curve: section({ key: "drawdown_curve" }),
  returns_series: section({ key: "returns_series" }),
  vami: section({ key: "vami" }),
  monthly_returns: section({ key: "monthly_returns" }),
  period_tables: section({ key: "period_tables" }),
  trade_calendar: section({ key: "trade_calendar" }),
  streaks: section({ key: "streaks" }),
  distribution: section({ key: "distribution" }),
  histogram: section({ key: "histogram" }),
  outliers: section({ key: "outliers" }),
  excursions: section({ key: "excursions" }),
  duration: section({ key: "duration" }),
  grouped_performance: section({ key: "grouped_performance" }),
  benchmark: section({ key: "benchmark" }),
  costs: section({ key: "costs" }),
  warnings: [{ code: "short_sample", message: "Sample is short." }],
  quality_flags: [{ code: "gap", detail: "One market data gap." }],
  lineage: {
    engine_version: "2.4.0",
    config_hash: "cfg-hash",
    data_hash: "data-hash",
    request_hash: "req-hash",
  },
  truncation: [],
  non_binding: true,
};

describe("AnalyticsLibrary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listRuns.mockResolvedValue({ status: "success", data: { runs: [ENTRY] } });
    archiveRun.mockResolvedValue({
      status: "success",
      data: { ...ENTRY, archive_state: "archived" },
    });
  });

  it("reads the first catalogue page from the server", async () => {
    render(<AnalyticsLibrary />);
    await screen.findByText("canonical-1");
    expect(listRuns).toHaveBeenCalledWith({
      page: 1,
      page_size: LIBRARY_PAGE_SIZE,
    });
  });

  it("advances pages through the server, not the client", async () => {
    listRuns.mockResolvedValue({
      status: "success",
      data: {
        runs: Array.from({ length: LIBRARY_PAGE_SIZE }, (_unused, index) => ({
          ...ENTRY,
          run_id: `canonical-${index}`,
        })),
      },
    });
    render(<AnalyticsLibrary />);
    await screen.findByText("canonical-0");

    fireEvent.click(screen.getByRole("button", { name: /next page/i }));
    await waitFor(() =>
      expect(listRuns).toHaveBeenLastCalledWith({
        page: 2,
        page_size: LIBRARY_PAGE_SIZE,
      }),
    );
  });

  it("archives through the server and never offers a delete action", async () => {
    render(<AnalyticsLibrary />);
    await screen.findByText("canonical-1");

    fireEvent.click(screen.getByRole("button", { name: /^archive$/i }));
    await waitFor(() =>
      expect(archiveRun).toHaveBeenCalledWith("canonical-1", {
        archive_state: "archived",
      }),
    );
    expect(await screen.findByRole("button", { name: /unarchive/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /delete/i })).toBeNull();
  });

  it("surfaces a catalogue read failure instead of an empty list", async () => {
    listRuns.mockResolvedValue({
      status: "error",
      error: { message: "catalogue unavailable" },
    });
    render(<AnalyticsLibrary />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "catalogue unavailable",
    );
  });
});

describe("OverviewPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getRun.mockResolvedValue({ status: "success", data: ENTRY });
    getWorkbenchPayload.mockResolvedValue({ status: "success", data: PAYLOAD });
  });

  it("renders owner identity fields including lineage hashes", async () => {
    render(<OverviewPanel runId="canonical-1" />);
    expect(await screen.findByText("cfg-hash")).toBeInTheDocument();
    expect(screen.getByText("data-hash")).toBeInTheDocument();
    expect(screen.getByText("req-hash")).toBeInTheDocument();
    expect(screen.getByText("2.4.0")).toBeInTheDocument();
  });

  it("renders calculated metrics with their owner units", async () => {
    render(<OverviewPanel runId="canonical-1" />);
    const value = await screen.findByText("1234.50");
    expect(value.parentElement).toHaveTextContent("1234.50 USD");
  });

  it("marks a metric the report omitted as unavailable, never zero", async () => {
    render(<OverviewPanel runId="canonical-1" />);
    await screen.findByText("1234.50");

    const group = screen.getByRole("heading", { name: "Risk" }).parentElement;
    expect(group).not.toBeNull();
    const unavailable = within(group as HTMLElement).getAllByText("Unavailable");
    expect(unavailable.length).toBeGreaterThan(0);
    expect(within(group as HTMLElement).queryByText("0")).toBeNull();
  });

  it("preserves a non-default source context", async () => {
    render(<OverviewPanel runId="canonical-1" />);
    expect(await screen.findByText("(long)")).toBeInTheDocument();
  });

  it("renders quality flags and caveats supplied by the owner", async () => {
    render(<OverviewPanel runId="canonical-1" />);
    expect(await screen.findByText(/One market data gap\./)).toBeInTheDocument();
    expect(screen.getByText("Sample is short.")).toBeInTheDocument();
  });

  it("reports an unavailable projection instead of rendering empty metrics", async () => {
    getWorkbenchPayload.mockResolvedValue({
      status: "error",
      error: { message: "report artifact missing" },
    });
    render(<OverviewPanel runId="canonical-1" />);
    const alerts = await screen.findAllByRole("alert");
    expect(
      alerts.some((alert) =>
        alert.textContent?.includes("report artifact missing"),
      ),
    ).toBe(true);
    expect(screen.queryByText("1234.50")).toBeNull();
  });
});
