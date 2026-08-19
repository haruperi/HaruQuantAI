/**
 * Analytics overview panel (FEAT-UI-32).
 *
 * Renders run identity, report status, and the Analytics-owned metric groups
 * for one run. Every figure comes from the owner projection: a metric the
 * report omits is presented as unavailable, never as zero.
 */

"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  type AnalyticsWorkbenchPayload,
  type RunCatalogueEntry,
} from "@/clients";
import { AnalyticsEvidenceState, EvidenceValue } from "./AnalyticsEvidenceState";

/**
 * Ordered metric groups exactly as the Analytics overview specifies.
 *
 * Each group lists the summary keys it may contain. A key absent from the
 * owner's summary section is rendered as unavailable rather than omitted, so a
 * reader can tell "not calculated" apart from "not requested".
 */
export const METRIC_GROUPS: readonly (readonly [string, readonly string[]])[] = [
  [
    "Profitability and PnL",
    ["net_pnl", "gross_profit", "gross_loss", "starting_equity", "ending_equity"],
  ],
  [
    "Trade statistics",
    ["trade_count", "win_rate", "profit_factor", "payoff_ratio", "expectancy"],
  ],
  ["Returns", ["total_return", "cagr", "average_return", "best_return", "worst_return"]],
  ["Ratios", ["sharpe_ratio", "sortino_ratio", "calmar_ratio", "information_ratio"]],
  [
    "Drawdown",
    ["max_drawdown", "max_drawdown_duration", "average_drawdown", "recovery_factor"],
  ],
  ["Risk", ["volatility", "downside_deviation", "value_at_risk", "ulcer_index"]],
  [
    "Costs and efficiency",
    ["total_commission", "total_swap", "total_cost_drag", "average_trade_duration"],
  ],
  [
    "Benchmark",
    [
      "benchmark_alpha",
      "benchmark_beta",
      "benchmark_correlation",
      "tracking_error",
    ],
  ],
  ["Statistical", ["skewness", "kurtosis", "sample_count", "observation_count"]],
];

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The Analytics workbench projection is unavailable.";
}

/** Read one string field from an owner-supplied mapping. */
function field(source: Record<string, unknown> | undefined, key: string): unknown {
  if (!source) return undefined;
  return source[key];
}

/** Props accepted by `OverviewPanel`. */
export interface OverviewPanelProps {
  runId: string;
  className?: string;
}

/** Run identity, report status, and owner metric groups for one run. */
export function OverviewPanel({
  runId,
  className = "",
}: OverviewPanelProps): ReactNode {
  const [entry, setEntry] = useState<RunCatalogueEntry | null>(null);
  const [payload, setPayload] = useState<AnalyticsWorkbenchPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const [runResponse, payloadResponse] = await Promise.all([
        apiClients.analyticsWorkbench.getRun(id),
        apiClients.analyticsWorkbench.getWorkbenchPayload(id),
      ]);
      if (runResponse.status === "error") {
        setError(runResponse.error.message);
        return;
      }
      setEntry(runResponse.data);
      if (payloadResponse.status === "error") {
        setError(payloadResponse.error.message);
        return;
      }
      setPayload(payloadResponse.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(runId);
  }, [load, runId]);

  /** Owner summary rows keyed by metric name. */
  const summaryByKey = useMemo(() => {
    const found = new Map<string, Record<string, unknown>>();
    for (const item of payload?.summary.items ?? []) {
      const key = item.key ?? item.name ?? item.metric;
      if (typeof key === "string") found.set(key, item);
    }
    return found;
  }, [payload]);

  const lineage = (payload?.lineage ?? {}) as Record<string, unknown>;

  return (
    <section
      className={`analytics-overview ${className}`.trim()}
      aria-label="Analytics overview"
    >
      {loading ? <p role="status">Loading run overview…</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      {entry ? (
        <section aria-labelledby="analytics-overview-identity">
          <h3 id="analytics-overview-identity">Run identity</h3>
          <dl className="analytics-overview__identity">
            <dt>Run ID</dt>
            <dd className="font-mono">{entry.run_id}</dd>
            <dt>Report ID</dt>
            <dd className="font-mono">
              <EvidenceValue value={entry.report_id} />
            </dd>
            <dt>Strategy</dt>
            <dd>
              {entry.strategy_label ?? entry.strategy_id}
              {entry.strategy_version ? ` (${entry.strategy_version})` : ""}
            </dd>
            <dt>Measurement window</dt>
            <dd>
              {entry.measurement_start} → {entry.measurement_end}
            </dd>
            <dt>Engine version</dt>
            <dd>
              <EvidenceValue value={field(lineage, "engine_version")} />
            </dd>
            <dt>Config hash</dt>
            <dd className="font-mono">
              <EvidenceValue value={field(lineage, "config_hash")} />
            </dd>
            <dt>Data hash</dt>
            <dd className="font-mono">
              <EvidenceValue value={field(lineage, "data_hash")} />
            </dd>
            <dt>Request hash</dt>
            <dd className="font-mono">
              <EvidenceValue value={field(lineage, "request_hash")} />
            </dd>
            <dt>Evidence class</dt>
            <dd>{entry.evidence_class}</dd>
          </dl>
        </section>
      ) : null}

      {payload ? (
        <section aria-labelledby="analytics-overview-status">
          <h3 id="analytics-overview-status">Report status</h3>
          <p>
            This report is advisory evidence and is marked non-binding by its
            owner.
          </p>
          <p>Summary section: {payload.summary.status}</p>
          <p>Curve basis: {payload.equity_curve.source_context}</p>
          <p>Sample adequacy: {payload.summary.sample_count} summary samples</p>

          <h4>Quality flags</h4>
          {payload.quality_flags.length > 0 ? (
            <ul>
              {payload.quality_flags.map((flag, index) => (
                <li key={`${String(flag.code ?? index)}`}>
                  {String(flag.code ?? flag.name ?? "flag")}:{" "}
                  {String(flag.detail ?? flag.message ?? "")}
                </li>
              ))}
            </ul>
          ) : (
            <p>No quality flag was raised.</p>
          )}

          <h4>Caveats</h4>
          {payload.warnings.length > 0 ? (
            <ul>
              {payload.warnings.map((warning, index) => (
                <li key={`${String(warning.code ?? index)}`}>
                  {String(warning.message ?? warning.detail ?? warning.code ?? "")}
                </li>
              ))}
            </ul>
          ) : (
            <p>No caveat was recorded.</p>
          )}

          {payload.truncation.length > 0 ? (
            <>
              <h4>Truncation</h4>
              <ul>
                {payload.truncation.map((item, index) => (
                  <li key={`${String(item.section ?? index)}`}>
                    {String(item.section ?? "section")}: {String(item.retained ?? "")}
                    {" of "}
                    {String(item.total ?? "")}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </section>
      ) : null}

      <section aria-labelledby="analytics-overview-metrics">
        <h3 id="analytics-overview-metrics">Core metrics</h3>
        <AnalyticsEvidenceState
          loading={loading}
          error={error}
          section={payload?.summary ?? null}
          label="Summary metrics"
        >
          {METRIC_GROUPS.map(([group, keys]) => (
            <section key={group}>
              <h4>{group}</h4>
              <dl className="analytics-overview__metrics">
                {keys.map((key) => {
                  const row = summaryByKey.get(key);
                  return (
                    <div key={key} className="analytics-overview__metric">
                      <dt>{String(row?.label ?? key)}</dt>
                      <dd>
                        <EvidenceValue
                          value={row?.value}
                          unit={
                            typeof row?.unit === "string" ? row.unit : undefined
                          }
                        />
                        {typeof row?.source_context === "string" &&
                        row.source_context !== "all" ? (
                          <span className="analytics-overview__context">
                            {" "}
                            ({row.source_context})
                          </span>
                        ) : null}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </section>
          ))}
        </AnalyticsEvidenceState>
      </section>
    </section>
  );
}
