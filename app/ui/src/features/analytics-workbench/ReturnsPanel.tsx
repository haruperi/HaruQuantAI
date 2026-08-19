/**
 * Returns and VAMI panel (FEAT-UI-32).
 *
 * Renders the Analytics-owned returns series, VAMI, and monthly returns. A
 * metric the V2 catalogue does not calculate is stated as such in the exact
 * agreed wording rather than being approximated from adjacent figures.
 */

"use client";

import type { ReactNode } from "react";

import type { AnalyticsWorkbenchPayload } from "@/clients";
import {
  AnalyticsEvidenceState,
  EVIDENCE_UNAVAILABLE_TEXT,
  EvidenceValue,
} from "./AnalyticsEvidenceState";
import { TimeSeriesChart } from "./TimeSeriesChart";

/** Summary keys the returns view reads from the owner projection. */
export const RETURNS_METRICS: readonly (readonly [string, string])[] = [
  ["net_pnl", "Net PnL"],
  ["total_return", "Total return"],
  ["cagr", "CAGR"],
  ["average_return", "Average return"],
  ["best_return", "Best period return"],
  ["worst_return", "Worst period return"],
];

/**
 * Metrics the V2 catalogue deliberately does not calculate.
 *
 * They are listed rather than hidden so a reader migrating from V1 can see
 * that their absence is a decision, not an outage.
 */
export const UNSUPPORTED_RETURNS_METRICS: readonly string[] = [
  "Risk of ruin",
  "System Quality Number",
  "Deflated Sharpe ratio",
  "Deflated Sharpe p-value",
];

/** Read one owner summary row by key. */
export function summaryRow(
  payload: AnalyticsWorkbenchPayload | null,
  key: string,
): Record<string, unknown> | undefined {
  for (const item of payload?.summary.items ?? []) {
    if (item.key === key || item.name === key || item.metric === key) {
      return item;
    }
  }
  return undefined;
}

/** Render the frozen unsupported-metric list. */
export function UnsupportedMetrics({
  metrics,
}: {
  metrics: readonly string[];
}): ReactNode {
  return (
    <section aria-label="Unsupported metrics">
      <h4>Not calculated by V2</h4>
      <dl className="analytics-overview__metrics">
        {metrics.map((metric) => (
          <div key={metric} className="analytics-overview__metric">
            <dt>{metric}</dt>
            <dd>{EVIDENCE_UNAVAILABLE_TEXT}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

/** Props shared by the advanced Analytics evidence panels. */
export interface AdvancedPanelProps {
  payload: AnalyticsWorkbenchPayload | null;
  loading?: boolean;
  error?: string | null;
  className?: string;
}

/** Returns, cumulative growth, and monthly performance for one run. */
export function ReturnsPanel({
  payload,
  loading = false,
  error = null,
  className = "",
}: AdvancedPanelProps): ReactNode {
  return (
    <section
      className={`analytics-returns ${className}`.trim()}
      aria-label="Returns and VAMI"
    >
      <h3>Returns</h3>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.summary ?? null}
        label="Return metrics"
      >
        <dl className="analytics-overview__metrics">
          {RETURNS_METRICS.map(([key, label]) => {
            const row = summaryRow(payload, key);
            return (
              <div key={key} className="analytics-overview__metric">
                <dt>{label}</dt>
                <dd>
                  <EvidenceValue
                    value={row?.value}
                    unit={typeof row?.unit === "string" ? row.unit : undefined}
                  />
                </dd>
              </div>
            );
          })}
        </dl>
      </AnalyticsEvidenceState>

      <TimeSeriesChart
        section={payload?.returns_series ?? null}
        title="Returns series"
      />
      <TimeSeriesChart section={payload?.vami ?? null} title="VAMI" />
      <TimeSeriesChart
        section={payload?.monthly_returns ?? null}
        title="Monthly returns"
        labelKey="period"
      />

      <UnsupportedMetrics metrics={UNSUPPORTED_RETURNS_METRICS} />
    </section>
  );
}
