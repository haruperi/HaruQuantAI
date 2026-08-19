/**
 * Distribution and statistics panel (FEAT-UI-32).
 *
 * Renders the Analytics-owned distribution, histogram, outliers, excursions,
 * and duration sections. The panel bins nothing and flags no outlier of its
 * own: an outlier is only an outlier because the owner said so.
 */

"use client";

import type { ReactNode } from "react";

import {
  AnalyticsEvidenceState,
  EvidenceValue,
} from "./AnalyticsEvidenceState";
import { DistributionChart } from "./DistributionChart";
import {
  UnsupportedMetrics,
  summaryRow,
  type AdvancedPanelProps,
} from "./ReturnsPanel";

/** Summary keys the statistics view reads from the owner projection. */
export const DISTRIBUTION_METRICS: readonly (readonly [string, string])[] = [
  ["skewness", "Skewness"],
  ["kurtosis", "Kurtosis"],
  ["expectancy", "Expectancy"],
  ["payoff_ratio", "Payoff ratio"],
  ["sample_count", "Sample count"],
];

/** Statistics the V2 catalogue deliberately does not calculate. */
export const UNSUPPORTED_DISTRIBUTION_METRICS: readonly string[] = [
  "Deflated Sharpe ratio",
  "Deflated Sharpe p-value",
  "Browser Monte Carlo distribution",
];

/** Render one owner section as a generic evidence table. */
function SectionTable({
  items,
  columns,
}: {
  items: readonly Record<string, unknown>[];
  columns: readonly string[];
}): ReactNode {
  return (
    <table className="analytics-library__table">
      <caption className="sr-only">Owner-reported rows</caption>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column} scope="col">
              {column}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.map((item, index) => (
          <tr key={index}>
            {columns.map((column) => (
              <td key={column}>{String(item[column] ?? "—")}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Distribution, excursions, duration, and outlier evidence for one run. */
export function DistributionPanel({
  payload,
  loading = false,
  error = null,
  className = "",
}: AdvancedPanelProps): ReactNode {
  return (
    <section
      className={`analytics-distribution-panel ${className}`.trim()}
      aria-label="Distribution and statistics"
    >
      <h3>Distribution and statistics</h3>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.summary ?? null}
        label="Statistical metrics"
      >
        <dl className="analytics-overview__metrics">
          {DISTRIBUTION_METRICS.map(([key, label]) => {
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

      <DistributionChart
        section={payload?.histogram ?? null}
        title="PnL histogram"
      />
      <DistributionChart
        section={payload?.distribution ?? null}
        title="Return distribution"
      />

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.outliers ?? null}
        label="Outliers"
      >
        <SectionTable
          items={payload?.outliers.items ?? []}
          columns={["ticket", "value", "reason"]}
        />
      </AnalyticsEvidenceState>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.excursions ?? null}
        label="Excursions"
      >
        <SectionTable
          items={payload?.excursions.items ?? []}
          columns={["ticket", "mae", "mfe"]}
        />
      </AnalyticsEvidenceState>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.duration ?? null}
        label="Holding duration"
      >
        <SectionTable
          items={payload?.duration.items ?? []}
          columns={["bucket", "count"]}
        />
      </AnalyticsEvidenceState>

      <UnsupportedMetrics metrics={UNSUPPORTED_DISTRIBUTION_METRICS} />
    </section>
  );
}
