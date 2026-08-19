/**
 * Analytics run comparison (FEAT-UI-32).
 *
 * Selects runs and asks Analytics to compare them. The comparison itself is
 * always the owner's: this surface never subtracts two payloads to produce a
 * difference, because an arbitrary JSON subtraction would present an invented
 * number with the same authority as a measured one.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  COMPARISON_METRICS,
  type ComparisonEvidence,
  type ComparisonMetric,
  type RunCatalogueEntry,
} from "@/clients";
import {
  MAX_COMPARISON_RUNS,
  MIN_COMPARISON_RUNS,
  isComparable,
  toComparisonRows,
} from "./analytics-selectors";
import { useAnalyticsWorkbenchStore } from "./analytics-store";
import { EvidenceValue } from "./AnalyticsEvidenceState";

/** Resolve a failure message without implying a comparison succeeded. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The comparison is unavailable.";
}

/** Props accepted by `AnalyticsComparison`. */
export interface AnalyticsComparisonProps {
  initialRunIds?: readonly string[];
  className?: string;
}

/** Owner-delegated comparison across a bounded run selection. */
export function AnalyticsComparison({
  initialRunIds,
  className = "",
}: AnalyticsComparisonProps): ReactNode {
  const selectedRunIds = useAnalyticsWorkbenchStore(
    (state) => state.selectedRunIds,
  );
  const metric = useAnalyticsWorkbenchStore((state) => state.metric);
  const setMetric = useAnalyticsWorkbenchStore((state) => state.setMetric);
  const toggleRun = useAnalyticsWorkbenchStore((state) => state.toggleRun);
  const setSelection = useAnalyticsWorkbenchStore(
    (state) => state.setSelection,
  );

  const [runs, setRuns] = useState<RunCatalogueEntry[]>([]);
  const [evidence, setEvidence] = useState<ComparisonEvidence | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    if (initialRunIds && initialRunIds.length > 0) {
      setSelection(initialRunIds);
    }
  }, [initialRunIds, setSelection]);

  useEffect(() => {
    let cancelled = false;
    void apiClients.analyticsWorkbench
      .listRuns({ page: 1, page_size: 50 })
      .then((response) => {
        if (cancelled || response.status === "error") return;
        setRuns(response.data.runs);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const compare = useCallback(async () => {
    if (!isComparable(selectedRunIds) || comparing) return;
    setComparing(true);
    setError(null);
    try {
      const response = await apiClients.analyticsWorkbench.compareRuns({
        run_ids: [...selectedRunIds],
        metric,
      });
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setEvidence(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setComparing(false);
    }
  }, [selectedRunIds, metric, comparing]);

  const rows = toComparisonRows(evidence);

  return (
    <section
      className={`analytics-comparison ${className}`.trim()}
      aria-label="Run comparison"
    >
      <h3>Compare runs</h3>
      <p className="analytics-library__note">
        Comparison evidence is produced by Analytics. This view selects runs
        and renders the result; it computes no difference of its own.
      </p>

      <div className="analytics-comparison__controls">
        <label htmlFor="comparison-metric">Metric group</label>
        <select
          id="comparison-metric"
          value={metric}
          onChange={(event) =>
            setMetric(event.target.value as ComparisonMetric)
          }
        >
          {COMPARISON_METRICS.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={() => void compare()}
          disabled={!isComparable(selectedRunIds) || comparing}
        >
          {comparing ? "Comparing…" : "Compare selected runs"}
        </button>

        <span>
          {selectedRunIds.length} of {MAX_COMPARISON_RUNS} selected (minimum{" "}
          {MIN_COMPARISON_RUNS})
        </span>
      </div>

      <fieldset className="analytics-comparison__selection">
        <legend>Runs</legend>
        {runs.map((run) => (
          <label key={run.run_id}>
            <input
              type="checkbox"
              checked={selectedRunIds.includes(run.run_id)}
              onChange={() => toggleRun(run.run_id)}
            />
            <span>
              {run.name ?? run.run_id} ({run.evidence_class})
            </span>
          </label>
        ))}
      </fieldset>

      {error ? <p role="alert">{error}</p> : null}

      {evidence ? (
        <table className="analytics-library__table" aria-label="Comparison evidence">
          <caption className="sr-only">
            Owner comparison for {evidence.metric}
          </caption>
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Metric</th>
              <th scope="col">Value</th>
              <th scope="col">Context</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.runId}-${row.label}`}>
                <td className="font-mono">{row.runId}</td>
                <td>{row.label}</td>
                <td>
                  <EvidenceValue value={row.value} unit={row.unit} />
                </td>
                <td>{row.context}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
