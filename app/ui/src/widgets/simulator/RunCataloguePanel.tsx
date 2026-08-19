/**
 * Historical run catalogue pane (FEAT-UI-31).
 *
 * Lists the caller's recorded simulation runs, newest first, and hands each
 * one off to the Analytics workspace. Every value shown is server evidence:
 * the panel never derives a status, a metric, or an outcome of its own.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients, type RunCatalogueEntry } from "@/clients";
import { useAnalyticsWorkbenchStore } from "@/widgets/analytics/analytics-store";
import { useWorkspaceStore } from "@/widgets/workspaces";

/** Page size requested from the catalogue; the server bounds the maximum. */
export const CATALOGUE_PAGE_SIZE = 25;

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The run catalogue is unavailable.";
}

/** Render one ISO timestamp as its date portion, or a dash. */
function toDate(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : "—";
}

/** Props accepted by `RunCataloguePanel`. */
export interface RunCataloguePanelProps {
  onOpenAnalytics?: (runId: string) => void;
  className?: string;
}

/** Server-paginated catalogue of the caller's recorded simulation runs. */
export function RunCataloguePanel({
  onOpenAnalytics,
  className = "",
}: RunCataloguePanelProps = {}): ReactNode {
  const [runs, setRuns] = useState<RunCatalogueEntry[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleOpenAnalytics = useCallback(
    (runId: string) => {
      if (onOpenAnalytics) {
        onOpenAnalytics(runId);
        return;
      }
      useAnalyticsWorkbenchStore.getState().setSelection([runId]);
      useWorkspaceStore
        .getState()
        .addWidgetToWorkspace("analytics", `Analytics: ${runId}`, undefined, undefined, runId);
    },
    [onOpenAnalytics],
  );

  const load = useCallback(async (requested: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClients.analyticsWorkbench.listRuns({
        page: requested,
        page_size: CATALOGUE_PAGE_SIZE,
      });
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setRuns(response.data.runs);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(page);
  }, [load, page]);

  return (
    <section
      className={`simulation-catalogue ${className}`.trim()}
      aria-label="Run catalogue"
    >
      <h3>Run catalogue</h3>
      {error ? (
        <p className="simulation-catalogue__error" role="alert">
          {error}
        </p>
      ) : loading ? (
        <p className="simulation-catalogue__note">Loading recorded runs…</p>
      ) : runs.length === 0 ? (
        <p className="simulation-catalogue__note">No runs have been recorded yet.</p>
      ) : (
        <table className="simulation-catalogue__table">
          <caption className="sr-only">Recorded simulation run catalogue</caption>
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Strategy</th>
              <th scope="col">Symbols</th>
              <th scope="col">Window</th>
              <th scope="col">Origin</th>
              <th scope="col">Status</th>
              <th scope="col">Evidence</th>
              <th scope="col">Open</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((entry) => (
              <tr key={entry.run_id}>
                <td className="font-mono">{entry.run_id}</td>
                <td>{entry.strategy_label ?? entry.strategy_id}</td>
                <td>{entry.symbols.join(", ")}</td>
                <td>
                  {toDate(entry.measurement_start)} → {toDate(entry.measurement_end)}
                </td>
                <td>{entry.origin_kind}</td>
                <td>{entry.status}</td>
                <td>{entry.evidence_class}</td>
                <td>
                  <button
                    type="button"
                    className="text-teal-400 hover:text-teal-300 underline cursor-pointer text-xs bg-transparent border-0 p-0"
                    onClick={() => handleOpenAnalytics(entry.run_id)}
                  >
                    Open in Analytics
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <nav className="simulation-catalogue__pager" aria-label="Run catalogue pages">
        <button
          type="button"
          onClick={() => setPage((current) => Math.max(1, current - 1))}
          disabled={loading || page === 1}
        >
          Previous
        </button>
        <span>Page {page}</span>
        <button
          type="button"
          onClick={() => setPage((current) => current + 1)}
          disabled={loading || runs.length < CATALOGUE_PAGE_SIZE}
        >
          Next
        </button>
      </nav>
    </section>
  );
}
