/**
 * Curated chart gallery (FEAT-UI-32).
 *
 * One gallery grouped by subject rather than one route per chart. Every chart
 * declares its own source payload, unit, sample count, truncation, and
 * unavailable reason through the shared primitives, so an absent series is
 * visibly absent rather than an empty frame.
 */

"use client";

import type { ReactNode } from "react";

import type { AnalyticsWorkbenchPayload } from "@/clients";
import { TimeSeriesChart } from "./TimeSeriesChart";
import { CalendarHeatmap } from "./CalendarHeatmap";
import { DistributionChart } from "./DistributionChart";

/** Ordered chart groups exactly as the chart gallery specifies. */
export const CHART_GROUPS: readonly string[] = [
  "Equity and returns",
  "Risk",
  "Trades",
  "Grouped performance",
];

/** Props accepted by `ChartsPanel`. */
export interface ChartsPanelProps {
  payload: AnalyticsWorkbenchPayload | null;
  className?: string;
}

/** Grouped chart gallery over one run's owner projection. */
export function ChartsPanel({
  payload,
  className = "",
}: ChartsPanelProps): ReactNode {
  return (
    <section
      className={`analytics-charts ${className}`.trim()}
      aria-label="Chart gallery"
    >
      <h3>Charts</h3>

      <section aria-label="Equity and returns">
        <h4>Equity and returns</h4>
        <TimeSeriesChart
          section={payload?.equity_curve ?? null}
          title="Equity curve"
        />
        <TimeSeriesChart section={payload?.vami ?? null} title="VAMI" />
        <TimeSeriesChart
          section={payload?.monthly_returns ?? null}
          title="Period returns"
          labelKey="period"
        />
      </section>

      <section aria-label="Risk">
        <h4>Risk</h4>
        <TimeSeriesChart
          section={payload?.drawdown_curve ?? null}
          title="Drawdown"
        />
        <DistributionChart
          section={payload?.distribution ?? null}
          title="Risk distribution"
        />
      </section>

      <section aria-label="Trades">
        <h4>Trades</h4>
        <DistributionChart
          section={payload?.streaks ?? null}
          title="Consecutive wins and losses"
          bucketKey="kind"
          countKey="length"
        />
        <DistributionChart
          section={payload?.duration ?? null}
          title="Holding time"
        />
        <DistributionChart
          section={payload?.excursions ?? null}
          title="MAE and MFE"
          bucketKey="ticket"
          countKey="mfe"
        />
      </section>

      <section aria-label="Grouped performance">
        <h4>Grouped performance</h4>
        <DistributionChart
          section={payload?.grouped_performance ?? null}
          title="Grouped performance"
          bucketKey="group"
          countKey="value"
        />
        <CalendarHeatmap
          section={payload?.trade_calendar ?? null}
          title="Trade calendar"
        />
      </section>
    </section>
  );
}
