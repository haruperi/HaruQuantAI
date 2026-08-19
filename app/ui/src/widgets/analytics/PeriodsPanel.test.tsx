/**
 * Period, benchmark, and chart gallery tests (FEAT-UI-32, P6-T02).
 *
 * Period dimensions and contexts travel in query parameters on one route, and
 * every chart declares its own owner payload rather than owning a route.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getPeriods } = vi.hoisted(() => ({ getPeriods: vi.fn() }));

vi.mock("@/clients", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    ApiClientError: class extends Error {},
    apiClients: { analyticsWorkbench: { getPeriods } },
  };
});

import { PeriodsPanel } from "./PeriodsPanel";
import { BenchmarkPanel } from "./BenchmarkPanel";
import { ChartsPanel } from "./ChartsPanel";

/** Build one owner section fixture. */
function section(key: string, overrides: Record<string, unknown> = {}) {
  return {
    key,
    status: "completed" as const,
    unit: null,
    source_context: "all",
    sample_count: 1,
    reason: null,
    truncated: false,
    total_count: 1,
    items: [],
    ...overrides,
  };
}

const PAYLOAD = {
  contract_version: "v1" as const,
  schema_id: "analytics.workbench_payload.v1" as const,
  payload_id: "payload-1",
  report_id: "report-1",
  generated_at: "2026-01-02T00:11:00Z",
  summary: section("summary", {
    items: [
      { key: "benchmark_alpha", value: "0.021", unit: "ratio" },
      { key: "total_cost_drag", value: "-88.40", unit: "USD" },
    ],
  }),
  equity_curve: section("equity_curve"),
  drawdown_curve: section("drawdown_curve"),
  returns_series: section("returns_series"),
  vami: section("vami"),
  monthly_returns: section("monthly_returns"),
  period_tables: section("period_tables"),
  trade_calendar: section("trade_calendar", {
    items: [{ date: "2025-03-04", value: 3 }],
  }),
  streaks: section("streaks"),
  distribution: section("distribution"),
  histogram: section("histogram"),
  outliers: section("outliers"),
  excursions: section("excursions"),
  duration: section("duration"),
  grouped_performance: section("grouped_performance"),
  benchmark: section("benchmark", {
    items: [
      {
        period: "2025-03",
        strategy_return: "0.031",
        benchmark_return: "0.012",
        excess_return: "0.019",
      },
    ],
  }),
  costs: section("costs"),
  warnings: [],
  quality_flags: [],
  lineage: {},
  truncation: [],
  non_binding: true as const,
};

describe("PeriodsPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPeriods.mockResolvedValue({
      status: "success",
      data: {
        run_id: "canonical-1",
        dimension: "month",
        context: "all",
        section: section("period_tables", {
          items: [
            { period: "2025-03", return: "0.031", pnl: "310.00", trades: 12 },
          ],
        }),
      },
    });
  });

  it("requests the period table with explicit dimension and context", async () => {
    render(<PeriodsPanel runId="canonical-1" payload={PAYLOAD} />);
    await waitFor(() =>
      expect(getPeriods).toHaveBeenCalledWith("canonical-1", {
        dimension: "month",
        context: "all",
      }),
    );
    await screen.findByText("2025-03");
  });

  it("reports a dimension change as a query change, not a new route", async () => {
    const onQueryChange = vi.fn();
    render(
      <PeriodsPanel
        runId="canonical-1"
        payload={PAYLOAD}
        onQueryChange={onQueryChange}
      />,
    );
    await screen.findByText("2025-03");
    fireEvent.change(screen.getByLabelText("Dimension"), {
      target: { value: "day_of_week" },
    });
    expect(onQueryChange).toHaveBeenCalledWith({
      dimension: "day_of_week",
      context: "all",
    });
  });

  it("reports a context change alongside the current dimension", async () => {
    const onQueryChange = vi.fn();
    render(
      <PeriodsPanel
        runId="canonical-1"
        payload={PAYLOAD}
        dimension="day_of_week"
        onQueryChange={onQueryChange}
      />,
    );
    await screen.findByText("2025-03");
    fireEvent.change(screen.getByLabelText("Context"), {
      target: { value: "short" },
    });
    expect(onQueryChange).toHaveBeenCalledWith({
      dimension: "day_of_week",
      context: "short",
    });
  });

  it("renders the owner period rows", async () => {
    render(<PeriodsPanel runId="canonical-1" payload={PAYLOAD} />);
    expect(await screen.findByText("2025-03")).toBeInTheDocument();
    expect(screen.getByText("310.00")).toBeInTheDocument();
  });

  it("reports an unavailable period table with the owner's reason", async () => {
    getPeriods.mockResolvedValue({
      status: "success",
      data: {
        run_id: "canonical-1",
        dimension: "month",
        context: "all",
        section: section("period_tables", {
          status: "unavailable",
          reason: "authoritative_evidence_unavailable",
        }),
      },
    });
    render(<PeriodsPanel runId="canonical-1" payload={PAYLOAD} />);
    expect(
      await screen.findByText(/authoritative_evidence_unavailable/),
    ).toBeInTheDocument();
  });
});

describe("BenchmarkPanel", () => {
  it("renders owner benchmark metrics and rows", () => {
    render(<BenchmarkPanel payload={PAYLOAD} />);
    expect(screen.getByText("0.021")).toBeInTheDocument();
    expect(screen.getByText("0.019")).toBeInTheDocument();
  });

  it("renders owner cost figures with their units", () => {
    render(<BenchmarkPanel payload={PAYLOAD} />);
    const value = screen.getByText("-88.40");
    expect(value.parentElement).toHaveTextContent("-88.40 USD");
  });

  it("marks the benchmark unavailable when the owner supplied none", () => {
    render(
      <BenchmarkPanel
        payload={{
          ...PAYLOAD,
          benchmark: section("benchmark", {
            status: "unavailable",
            reason: "authoritative_evidence_unavailable",
          }),
        }}
      />,
    );
    expect(
      screen.getByText(
        /Benchmark comparison: authoritative_evidence_unavailable/,
      ),
    ).toBeInTheDocument();
  });
});

describe("ChartsPanel", () => {
  it("groups charts by subject instead of routing each one", () => {
    render(<ChartsPanel payload={PAYLOAD} />);
    for (const group of [
      "Equity and returns",
      "Risk",
      "Trades",
      "Grouped performance",
    ]) {
      expect(
        screen.getByRole("region", { name: group }),
      ).toBeInTheDocument();
    }
  });

  it("declares the owner payload behind each chart", () => {
    render(<ChartsPanel payload={PAYLOAD} />);
    const risk = screen.getByRole("region", { name: "Risk" });
    expect(within(risk).getByText(/Source: drawdown_curve/)).toBeInTheDocument();
    expect(within(risk).getByText(/Source: distribution/)).toBeInTheDocument();
  });
});
