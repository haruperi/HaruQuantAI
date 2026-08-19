/**
 * Advanced Analytics evidence tests (FEAT-UI-32, P6-T01).
 *
 * Unsupported metrics must render the exact agreed wording, and every
 * supported figure must come from the owner projection.
 */

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReturnsPanel, UNSUPPORTED_RETURNS_METRICS } from "./ReturnsPanel";
import { RiskPanel } from "./RiskPanel";
import { DistributionPanel } from "./DistributionPanel";
import { EVIDENCE_UNAVAILABLE_TEXT } from "./AnalyticsEvidenceState";

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
      { key: "cagr", label: "CAGR", value: "0.184", unit: "ratio" },
      { key: "max_drawdown", value: "-0.121", unit: "ratio" },
      { key: "skewness", value: "0.42", unit: null },
    ],
  }),
  equity_curve: section("equity_curve"),
  drawdown_curve: section("drawdown_curve", {
    items: [{ timestamp: "2025-01-01", value: -0.02 }],
  }),
  returns_series: section("returns_series", {
    items: [{ timestamp: "2025-01-01", value: 0.004 }],
  }),
  vami: section("vami"),
  monthly_returns: section("monthly_returns"),
  period_tables: section("period_tables"),
  trade_calendar: section("trade_calendar"),
  streaks: section("streaks", {
    items: [
      { kind: "win", length: 5, start: "2025-02-01", end: "2025-02-06" },
    ],
  }),
  distribution: section("distribution"),
  histogram: section("histogram", {
    items: [{ bucket: "0..100", count: 7 }],
  }),
  outliers: section("outliers", {
    items: [{ ticket: "1001", value: "-450.00", reason: "tail_loss" }],
  }),
  excursions: section("excursions", {
    items: [{ ticket: "1001", mae: "-4.2", mfe: "31.1" }],
  }),
  duration: section("duration", { items: [{ bucket: "0-4h", count: 12 }] }),
  grouped_performance: section("grouped_performance"),
  benchmark: section("benchmark"),
  costs: section("costs"),
  warnings: [],
  quality_flags: [],
  lineage: {},
  truncation: [],
  non_binding: true as const,
};

describe("ReturnsPanel", () => {
  it("renders owner return metrics with their units", () => {
    render(<ReturnsPanel payload={PAYLOAD} />);
    const value = screen.getByText("0.184");
    expect(value.parentElement).toHaveTextContent("0.184 ratio");
  });

  it("marks a return metric the owner omitted as unavailable", () => {
    render(<ReturnsPanel payload={PAYLOAD} />);
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
  });

  it("states unsupported metrics in the exact agreed wording", () => {
    render(<ReturnsPanel payload={PAYLOAD} />);
    const unsupported = screen.getByRole("region", {
      name: "Unsupported metrics",
    });
    for (const metric of UNSUPPORTED_RETURNS_METRICS) {
      expect(within(unsupported).getByText(metric)).toBeInTheDocument();
    }
    expect(
      within(unsupported).getAllByText(EVIDENCE_UNAVAILABLE_TEXT).length,
    ).toBe(UNSUPPORTED_RETURNS_METRICS.length);
  });

  it("plots only owner series", () => {
    render(<ReturnsPanel payload={PAYLOAD} />);
    expect(screen.getByText("Returns series")).toBeInTheDocument();
    expect(screen.getByText("VAMI")).toBeInTheDocument();
  });
});

describe("RiskPanel", () => {
  it("renders owner drawdown metrics", () => {
    render(<RiskPanel payload={PAYLOAD} />);
    expect(screen.getByText("-0.121")).toBeInTheDocument();
  });

  it("renders owner-reported streaks without deriving one", () => {
    render(<RiskPanel payload={PAYLOAD} />);
    expect(screen.getByText("win")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("names risk metrics V2 does not calculate", () => {
    render(<RiskPanel payload={PAYLOAD} />);
    const unsupported = screen.getByRole("region", {
      name: "Unsupported metrics",
    });
    expect(within(unsupported).getByText("Risk of ruin")).toBeInTheDocument();
  });
});

describe("DistributionPanel", () => {
  it("renders owner buckets, outliers, excursions, and durations", () => {
    render(<DistributionPanel payload={PAYLOAD} />);
    expect(screen.getByText("PnL histogram")).toBeInTheDocument();
    expect(screen.getByText("tail_loss")).toBeInTheDocument();
    expect(screen.getByText("31.1")).toBeInTheDocument();
    expect(screen.getByText("0-4h")).toBeInTheDocument();
  });

  it("renders owner statistics rather than deriving them", () => {
    render(<DistributionPanel payload={PAYLOAD} />);
    expect(screen.getByText("0.42")).toBeInTheDocument();
  });

  it("names statistics V2 does not calculate", () => {
    render(<DistributionPanel payload={PAYLOAD} />);
    const unsupported = screen.getByRole("region", {
      name: "Unsupported metrics",
    });
    expect(
      within(unsupported).getByText("Browser Monte Carlo distribution"),
    ).toBeInTheDocument();
  });

  it("reports an unavailable section with the owner's reason", () => {
    render(
      <DistributionPanel
        payload={{
          ...PAYLOAD,
          outliers: section("outliers", {
            status: "unavailable",
            reason: "authoritative_evidence_unavailable",
          }),
        }}
      />,
    );
    expect(
      screen.getByText(/Outliers: authoritative_evidence_unavailable/),
    ).toBeInTheDocument();
  });
});
