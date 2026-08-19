/**
 * Benchmark and cost panel (FEAT-UI-32).
 *
 * Renders the Analytics-owned benchmark comparison and cost drag. Relative
 * performance is only shown when the owner supplied a benchmark: comparing a
 * run against an unstated baseline would be a claim, not evidence.
 */

"use client";

import type { ReactNode } from "react";

import {
  AnalyticsEvidenceState,
  EvidenceValue,
} from "./AnalyticsEvidenceState";
import { summaryRow, type AdvancedPanelProps } from "./ReturnsPanel";

/** Benchmark metrics the owner may supply. */
export const BENCHMARK_METRICS: readonly (readonly [string, string])[] = [
  ["benchmark_alpha", "Alpha"],
  ["benchmark_beta", "Beta"],
  ["benchmark_correlation", "Correlation"],
  ["tracking_error", "Tracking error"],
  ["information_ratio", "Information ratio"],
];

/** Cost metrics the owner may supply. */
export const COST_METRICS: readonly (readonly [string, string])[] = [
  ["total_commission", "Commission"],
  ["total_swap", "Swap"],
  ["total_cost_drag", "Total cost drag"],
  ["average_trade_duration", "Average trade duration"],
];

/** Benchmark comparison and cost drag for one run. */
export function BenchmarkPanel({
  payload,
  loading = false,
  error = null,
  className = "",
}: AdvancedPanelProps): ReactNode {
  return (
    <section
      className={`analytics-benchmark ${className}`.trim()}
      aria-label="Benchmark and costs"
    >
      <h3>Benchmark and costs</h3>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.benchmark ?? null}
        label="Benchmark comparison"
      >
        <dl className="analytics-overview__metrics">
          {BENCHMARK_METRICS.map(([key, label]) => {
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

        <table className="analytics-library__table">
          <caption className="sr-only">Owner-reported benchmark rows</caption>
          <thead>
            <tr>
              <th scope="col">period</th>
              <th scope="col">strategy_return</th>
              <th scope="col">benchmark_return</th>
              <th scope="col">excess_return</th>
            </tr>
          </thead>
          <tbody>
            {(payload?.benchmark.items ?? []).map((item, index) => (
              <tr key={`${String(item.period ?? index)}`}>
                <td>{String(item.period ?? "—")}</td>
                <td>{String(item.strategy_return ?? "—")}</td>
                <td>{String(item.benchmark_return ?? "—")}</td>
                <td>{String(item.excess_return ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </AnalyticsEvidenceState>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.costs ?? null}
        label="Cost drag"
      >
        <dl className="analytics-overview__metrics">
          {COST_METRICS.map(([key, label]) => {
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
    </section>
  );
}
