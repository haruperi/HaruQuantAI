/**
 * Risk and drawdown panel (FEAT-UI-32).
 *
 * Renders the Analytics-owned drawdown curve, streaks, and risk metrics. Risk
 * figures V2 does not calculate are named explicitly rather than estimated
 * from the curve, because an estimated risk number reads as a measured one.
 */

"use client";

import type { ReactNode } from "react";

import {
  AnalyticsEvidenceState,
  EvidenceValue,
} from "./AnalyticsEvidenceState";
import { TimeSeriesChart } from "./TimeSeriesChart";
import {
  UnsupportedMetrics,
  summaryRow,
  type AdvancedPanelProps,
} from "./ReturnsPanel";

/** Summary keys the risk view reads from the owner projection. */
export const RISK_METRICS: readonly (readonly [string, string])[] = [
  ["max_drawdown", "Max drawdown"],
  ["max_drawdown_duration", "Max drawdown duration"],
  ["average_drawdown", "Average drawdown"],
  ["recovery_factor", "Recovery factor"],
  ["volatility", "Volatility (annualised)"],
  ["downside_deviation", "Downside deviation"],
  ["value_at_risk", "Value at risk"],
  ["ulcer_index", "Ulcer index"],
];

/** Risk metrics the V2 catalogue deliberately does not calculate. */
export const UNSUPPORTED_RISK_METRICS: readonly string[] = [
  "Risk of ruin",
  "Monte Carlo drawdown envelope",
  "Strategy scorecard verdict",
];

/** Drawdown, streaks, and risk statistics for one run. */
export function RiskPanel({
  payload,
  loading = false,
  error = null,
  className = "",
}: AdvancedPanelProps): ReactNode {
  return (
    <section
      className={`analytics-risk ${className}`.trim()}
      aria-label="Drawdown and risk"
    >
      <h3>Drawdown and risk</h3>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.summary ?? null}
        label="Risk metrics"
      >
        <dl className="analytics-overview__metrics">
          {RISK_METRICS.map(([key, label]) => {
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
        section={payload?.drawdown_curve ?? null}
        title="Drawdown curve"
      />

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={payload?.streaks ?? null}
        label="Win and loss streaks"
      >
        <table className="analytics-library__table">
          <caption className="sr-only">Owner-reported streaks</caption>
          <thead>
            <tr>
              <th scope="col">Kind</th>
              <th scope="col">Length</th>
              <th scope="col">Start</th>
              <th scope="col">End</th>
            </tr>
          </thead>
          <tbody>
            {(payload?.streaks.items ?? []).map((item, index) => (
              <tr key={`${String(item.kind ?? index)}-${index}`}>
                <td>{String(item.kind ?? "—")}</td>
                <td>{String(item.length ?? "—")}</td>
                <td>{String(item.start ?? "—")}</td>
                <td>{String(item.end ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </AnalyticsEvidenceState>

      <UnsupportedMetrics metrics={UNSUPPORTED_RISK_METRICS} />
    </section>
  );
}
