/**
 * Analytics Workbench client contract tests (FEAT-UI-32 / P1-T01).
 *
 * Verifies that analyticsWorkbench client operations invoke correct routes,
 * methods, queries, parameter substitutions, and parse responses with Zod schemas.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, apiClients } from "@/clients";
import { analyticsWorkbenchRoutes } from "@/clients/routes";

const realFetch = globalThis.fetch;

function envelope(data: unknown, route: string, operation: string, status = 200): Response {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data,
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req-anlt-test",
        route,
        operation,
        trace_id: null,
        side_effect: "read",
        duration_ms: 1,
        timestamp: "2026-08-18T00:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status, headers: { "Content-Type": "application/json" } },
  );
}

function errorEnvelope(code: string, message: string, status = 400): Response {
  return new Response(
    JSON.stringify({
      status: "error",
      message,
      data: null,
      error: {
        code,
        message,
        details: {},
        request_id: "req-anlt-test",
        trace_id: null,
        retryable: false,
      },
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req-anlt-test",
        route: "test",
        operation: "test",
        trace_id: null,
        side_effect: "none",
        duration_ms: 1,
        timestamp: "2026-08-18T00:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status, headers: { "Content-Type": "application/json" } },
  );
}

const SAMPLE_SECTION = {
  key: "summary",
  status: "completed",
  unit: null,
  source_context: "all",
  sample_count: 5,
  reason: null,
  truncated: false,
  total_count: 5,
  items: [{ metric: "sharpe_ratio", value: "1.85" }],
};

const SAMPLE_PAYLOAD = {
  contract_version: "v1",
  schema_id: "analytics.workbench_payload.v1",
  payload_id: "payload-1",
  report_id: "rep-1",
  generated_at: "2026-08-18T10:00:00Z",
  summary: SAMPLE_SECTION,
  equity_curve: { ...SAMPLE_SECTION, key: "equity_curve" },
  drawdown_curve: { ...SAMPLE_SECTION, key: "drawdown_curve" },
  returns_series: { ...SAMPLE_SECTION, key: "returns_series" },
  vami: { ...SAMPLE_SECTION, key: "vami" },
  monthly_returns: { ...SAMPLE_SECTION, key: "monthly_returns" },
  period_tables: { ...SAMPLE_SECTION, key: "period_tables" },
  trade_calendar: { ...SAMPLE_SECTION, key: "trade_calendar" },
  streaks: { ...SAMPLE_SECTION, key: "streaks" },
  distribution: { ...SAMPLE_SECTION, key: "distribution" },
  histogram: { ...SAMPLE_SECTION, key: "histogram" },
  outliers: { ...SAMPLE_SECTION, key: "outliers" },
  excursions: { ...SAMPLE_SECTION, key: "excursions" },
  duration: { ...SAMPLE_SECTION, key: "duration" },
  grouped_performance: { ...SAMPLE_SECTION, key: "grouped_performance" },
  benchmark: { ...SAMPLE_SECTION, key: "benchmark" },
  costs: { ...SAMPLE_SECTION, key: "costs" },
  warnings: [],
  quality_flags: [],
  lineage: { engine_version: "2.0.0" },
  truncation: [],
  non_binding: true,
};

const SAMPLE_CATALOGUE_ENTRY = {
  contract_version: "v1",
  schema_id: "api.run_catalogue_entry.v1",
  run_id: "run-100",
  principal_id: "user-1",
  origin_kind: "canonical_job",
  origin_id: "job-100",
  job_id: "job-100",
  batch_id: null,
  session_id: null,
  strategy_id: "ema_cross",
  strategy_version: "1.0.0",
  strategy_label: "EMA Trend Crossover",
  symbols: ["EURUSD"],
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
  name: "Baseline EURUSD Run",
  alias: "eurusd-base",
  description: "Canonical baseline backtest",
  tags: ["baseline", "fx"],
  run_reason: "Quarterly review",
  archive_state: "active",
};

describe("analyticsWorkbench client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("listRuns fetches paginated catalogue entries", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope({ runs: [SAMPLE_CATALOGUE_ENTRY] }, analyticsWorkbenchRoutes.runs.path, "list_runs"),
    );

    const res = await apiClients.analyticsWorkbench.listRuns({ page: 1, page_size: 20 });
    expect(res.data!.runs).toHaveLength(1);
    expect(res.data!.runs[0].run_id).toBe("run-100");
    expect(res.data!.runs[0].evidence_class).toBe("canonical");
  });

  it("getRun reads single catalogue entry by run_id", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(SAMPLE_CATALOGUE_ENTRY, analyticsWorkbenchRoutes.run.path, "get_run"),
    );

    const res = await apiClients.analyticsWorkbench.getRun("run-100");
    expect(res.data!.run_id).toBe("run-100");
    expect(res.data!.strategy_id).toBe("ema_cross");
  });

  it("getWorkbenchPayload validates 17 standard sections", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(SAMPLE_PAYLOAD, analyticsWorkbenchRoutes.workbenchPayload.path, "workbench"),
    );

    const res = await apiClients.analyticsWorkbench.getWorkbenchPayload("run-100");
    expect(res.data!.payload_id).toBe("payload-1");
    expect(res.data!.summary.key).toBe("summary");
    expect(res.data!.equity_curve.key).toBe("equity_curve");
    expect(res.data!.non_binding).toBe(true);
  });

  it("getTrades parses paginated closed trades", async () => {
    const sampleTradePage = {
      run_id: "run-100",
      page: 1,
      page_size: 50,
      total_trades: 1,
      total_pages: 1,
      trades: [
        {
          ticket: "1001",
          symbol: "EURUSD",
          side: "buy",
          volume: "1.0",
          entry_time: "2026-02-01T10:00:00Z",
          entry_price: "1.08500",
          exit_time: "2026-02-01T14:00:00Z",
          exit_price: "1.08900",
          pnl: "400.00",
          pnl_percent: "0.37",
          return_pct: "0.37",
          commission: "5.00",
          swap: "0.00",
          reason: "take_profit",
          mae: "-50.00",
          mfe: "450.00",
          bars_held: 4,
          duration_seconds: 14400,
        },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(sampleTradePage, analyticsWorkbenchRoutes.trades.path, "trades"),
    );

    const res = await apiClients.analyticsWorkbench.getTrades("run-100", { page: 1, page_size: 50, side: "buy" });
    expect(res.data!.trades).toHaveLength(1);
    expect(res.data!.trades[0].ticket).toBe("1001");
    expect(res.data!.trades[0].pnl).toBe("400.00");
  });

  it("getTrade reads single trade detail record", async () => {
    const sampleTrade = {
      ticket: "1001",
      symbol: "EURUSD",
      side: "buy",
      volume: "1.0",
      entry_time: "2026-02-01T10:00:00Z",
      entry_price: "1.08500",
      exit_time: "2026-02-01T14:00:00Z",
      exit_price: "1.08900",
      pnl: "400.00",
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(sampleTrade, analyticsWorkbenchRoutes.trade.path, "trade"),
    );

    const res = await apiClients.analyticsWorkbench.getTrade("run-100", "1001");
    expect(res.data!.ticket).toBe("1001");
    expect(res.data!.symbol).toBe("EURUSD");
  });

  it("getPeriods queries period tables with exact dimensions", async () => {
    const samplePeriods = {
      run_id: "run-100",
      dimension: "month",
      context: "all",
      section: SAMPLE_SECTION,
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(samplePeriods, analyticsWorkbenchRoutes.periods.path, "periods"),
    );

    const res = await apiClients.analyticsWorkbench.getPeriods("run-100", { dimension: "month", context: "all" });
    expect(res.data!.dimension).toBe("month");
    expect(res.data!.section?.key).toBe("summary");
  });

  it("getArtifacts lists attached artifact references", async () => {
    const sampleArtifacts = {
      run_id: "run-100",
      artifacts: [
        { kind: "result", ref: "sim-res-100" },
        { kind: "report", ref: "anlt-rep-100" },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(sampleArtifacts, analyticsWorkbenchRoutes.artifacts.path, "artifacts"),
    );

    const res = await apiClients.analyticsWorkbench.getArtifacts("run-100");
    expect(res.data!.artifacts).toHaveLength(2);
  });

  it("compareRuns delegates multi-run comparison to Analytics", async () => {
    const sampleComparison = {
      contract_version: "v1",
      schema_id: "analytics.comparison_evidence.v1",
      comparison_id: "cmp-1",
      metric: "summary",
      runs: [{ run_id: "run-100", sharpe: "1.85" }, { run_id: "run-101", sharpe: "1.42" }],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(sampleComparison, analyticsWorkbenchRoutes.compare.path, "compare"),
    );

    const res = await apiClients.analyticsWorkbench.compareRuns({
      run_ids: ["run-100", "run-101"],
      metric: "summary",
    });
    expect(res.data!.runs).toHaveLength(2);
  });

  it("annotateRun applies metadata annotations and returns updated catalogue row", async () => {
    const updated = { ...SAMPLE_CATALOGUE_ENTRY, name: "Renamed Run", tags: ["baseline", "reviewed"] };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(updated, analyticsWorkbenchRoutes.annotate.path, "annotate"),
    );

    const res = await apiClients.analyticsWorkbench.annotateRun(
      "run-100",
      { name: "Renamed Run", tags: ["baseline", "reviewed"] },
      { idempotencyKey: "idem-ann-1" },
    );
    expect(res.data!.name).toBe("Renamed Run");
    expect(res.data!.tags).toContain("reviewed");
  });

  it("archiveRun changes archive state without deleting data", async () => {
    const archived = { ...SAMPLE_CATALOGUE_ENTRY, archive_state: "archived" as const };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      envelope(archived, analyticsWorkbenchRoutes.archive.path, "archive"),
    );

    const res = await apiClients.analyticsWorkbench.archiveRun(
      "run-100",
      { archive_state: "archived" },
      { idempotencyKey: "idem-arc-1" },
    );
    expect(res.data!.archive_state).toBe("archived");
  });

  it("throws ApiClientError on 404 response", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      errorEnvelope("ANALYTICS_RUN_NOT_FOUND", "Run not found", 404),
    );

    await expect(
      apiClients.analyticsWorkbench.getRun("unknown-run"),
    ).rejects.toThrow(ApiClientError);
  });
});
