/**
 * Period aggregation panel (FEAT-UI-32).
 *
 * Every period dimension and context lives in the query string of the single
 * grouped route rather than in a route of its own. One route with explicit
 * parameters keeps a shared link reproducible and avoids a combinatorial
 * explosion of near-identical destinations.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  PERIOD_DIMENSIONS,
  type PeriodDimension,
  type PeriodTablePayload,
} from "@/clients";
import { AnalyticsEvidenceState } from "./AnalyticsEvidenceState";
import { CalendarHeatmap } from "./CalendarHeatmap";
import type { AnalyticsWorkbenchPayload } from "@/clients";

/** Source contexts the owner may supply for a period table. */
export const PERIOD_CONTEXTS = ["all", "long", "short"] as const;

/** One period source context. */
export type PeriodContext = (typeof PERIOD_CONTEXTS)[number];

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The period aggregation is unavailable.";
}

/** Props accepted by `PeriodsPanel`. */
export interface PeriodsPanelProps {
  runId: string;
  payload?: AnalyticsWorkbenchPayload | null;
  dimension?: PeriodDimension;
  context?: PeriodContext;
  onQueryChange?: (query: {
    dimension: PeriodDimension;
    context: PeriodContext;
  }) => void;
  className?: string;
}

/** Period tables and trade calendar for one run. */
export function PeriodsPanel({
  runId,
  payload = null,
  dimension = "month",
  context = "all",
  onQueryChange,
  className = "",
}: PeriodsPanelProps): ReactNode {
  const [table, setTable] = useState<PeriodTablePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClients.analyticsWorkbench.getPeriods(runId, {
        dimension,
        context,
      });
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setTable(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [runId, dimension, context]);

  useEffect(() => {
    void load();
  }, [load]);

  const columns = ["period", "return", "pnl", "trades", "win_rate"];

  return (
    <section
      className={`analytics-periods ${className}`.trim()}
      aria-label="Grouped performance"
    >
      <h3>Grouped performance</h3>

      <div className="analytics-periods__query">
        <label htmlFor="periods-dimension">Dimension</label>
        <select
          id="periods-dimension"
          value={dimension}
          onChange={(event) =>
            onQueryChange?.({
              dimension: event.target.value as PeriodDimension,
              context,
            })
          }
        >
          {PERIOD_DIMENSIONS.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <label htmlFor="periods-context">Context</label>
        <select
          id="periods-context"
          value={context}
          onChange={(event) =>
            onQueryChange?.({
              dimension,
              context: event.target.value as PeriodContext,
            })
          }
        >
          {PERIOD_CONTEXTS.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>

      <AnalyticsEvidenceState
        loading={loading}
        error={error}
        section={table?.section ?? null}
        label={`Period table (${dimension}, ${context})`}
      >
        <table className="analytics-library__table">
          <caption className="sr-only">
            Owner-reported {dimension} performance
          </caption>
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
            {(table?.section?.items ?? []).map((item, index) => (
              <tr key={`${String(item.period ?? index)}`}>
                {columns.map((column) => (
                  <td key={column}>{String(item[column] ?? "—")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </AnalyticsEvidenceState>

      <CalendarHeatmap
        section={payload?.trade_calendar ?? null}
        title="Trade calendar"
      />
    </section>
  );
}
