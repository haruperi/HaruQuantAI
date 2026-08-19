/**
 * Analytics chart primitive tests (FEAT-UI-32, P3-T03).
 *
 * Every chart must declare its source payload, unit, sample count, truncation
 * state, and unavailable reason, and must offer the same evidence as a table
 * without deriving any value of its own.
 */

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TimeSeriesChart, toSeriesPoints } from "./TimeSeriesChart";
import { CalendarHeatmap } from "./CalendarHeatmap";
import { DistributionChart } from "./DistributionChart";

/** Build one owner section fixture. */
function section(overrides: Record<string, unknown> = {}) {
  return {
    key: "equity_curve",
    status: "completed" as const,
    unit: "USD",
    source_context: "all",
    sample_count: 3,
    reason: null,
    truncated: false,
    total_count: 3,
    items: [
      { timestamp: "2025-01-01", value: 10000 },
      { timestamp: "2025-01-02", value: 10120 },
      { timestamp: "2025-01-03", value: 9980 },
    ],
    ...overrides,
  };
}

describe("TimeSeriesChart", () => {
  it("declares source, unit, sample count, and truncation state", () => {
    render(<TimeSeriesChart section={section()} title="Equity curve" />);
    expect(
      screen.getByText(
        "Source: equity_curve · Unit: USD · Samples: 3 · Not truncated",
      ),
    ).toBeInTheDocument();
  });

  it("declares truncation when the owner truncated the section", () => {
    render(
      <TimeSeriesChart
        section={section({ truncated: true, total_count: 9000 })}
        title="Equity curve"
      />,
    );
    expect(
      screen.getByText(/Truncated to 3 of 9000/),
    ).toBeInTheDocument();
  });

  it("renders the owner's exact unavailable reason", () => {
    render(
      <TimeSeriesChart
        section={section({
          status: "unavailable",
          reason: "authoritative_evidence_unavailable",
          items: [],
        })}
        title="Equity curve"
      />,
    );
    expect(
      screen.getByText("authoritative_evidence_unavailable"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("img")).toBeNull();
  });

  it("offers the same evidence as a table alternative", () => {
    render(<TimeSeriesChart section={section()} title="Equity curve" />);
    const table = screen.getByRole("table");
    expect(within(table).getByText("10120")).toBeInTheDocument();
    expect(within(table).getByText("2025-01-03")).toBeInTheDocument();
  });

  it("skips a non-numeric point instead of substituting zero", () => {
    const points = toSeriesPoints(
      [
        { timestamp: "a", value: 1 },
        { timestamp: "b", value: null },
        { timestamp: "c", value: "x" },
        { timestamp: "d", value: 2 },
      ],
      "value",
      "timestamp",
    );
    expect(points.map((point) => point.value)).toEqual([1, 2]);
  });
});

describe("CalendarHeatmap", () => {
  const calendar = section({
    key: "trade_calendar",
    unit: "trades",
    items: [
      { date: "2025-01-01", value: 3 },
      { date: "2025-01-02", value: null },
    ],
    sample_count: 2,
    total_count: 2,
  });

  it("declares its owner payload and unit", () => {
    render(<CalendarHeatmap section={calendar} title="Trade calendar" />);
    expect(
      screen.getByText(/Source: trade_calendar · Unit: trades · Samples: 2/),
    ).toBeInTheDocument();
  });

  it("marks a cell with no owner value as unavailable, not zero", () => {
    render(<CalendarHeatmap section={calendar} title="Trade calendar" />);
    const table = screen.getByRole("table");
    expect(within(table).getByText("Unavailable")).toBeInTheDocument();
    expect(within(table).queryByText("0")).toBeNull();
  });

  it("renders the owner's unavailable reason", () => {
    render(
      <CalendarHeatmap
        section={section({
          key: "trade_calendar",
          status: "unavailable",
          reason: "authoritative_evidence_unavailable",
          items: [],
        })}
        title="Trade calendar"
      />,
    );
    expect(
      screen.getByText("authoritative_evidence_unavailable"),
    ).toBeInTheDocument();
  });
});

describe("DistributionChart", () => {
  const histogram = section({
    key: "histogram",
    unit: "count",
    sample_count: 2,
    total_count: 2,
    items: [
      { bucket: "-100..0", count: 4 },
      { bucket: "0..100", count: 7 },
    ],
  });

  it("declares its owner payload and offers a table alternative", () => {
    render(<DistributionChart section={histogram} title="PnL distribution" />);
    expect(
      screen.getByText(/Source: histogram · Unit: count · Samples: 2/),
    ).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getByText("0..100")).toBeInTheDocument();
    expect(within(table).getByText("7")).toBeInTheDocument();
  });

  it("renders the owner's unavailable reason without a plot", () => {
    render(
      <DistributionChart
        section={section({
          key: "histogram",
          status: "unavailable",
          reason: "authoritative_evidence_unavailable",
          items: [],
        })}
        title="PnL distribution"
      />,
    );
    expect(
      screen.getByText("authoritative_evidence_unavailable"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("img")).toBeNull();
  });
});
