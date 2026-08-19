/**
 * Analytics run library (FEAT-UI-32).
 *
 * Lists the caller's catalogue runs from the server, page by page, with the
 * columns and actions the Analytics library specifies. Archiving is a metadata
 * transition only: no immutable owner artifact is ever deleted from this view.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  type RunCatalogueEntry,
} from "@/clients";

/** Server page size used by the library; the server bounds the maximum. */
export const LIBRARY_PAGE_SIZE = 50;

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The Analytics catalogue is unavailable.";
}

/** Render one ISO timestamp as its date portion, or a dash. */
function toDate(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : "—";
}

export interface AnalyticsLibraryProps {
  onSelectRun?: (runId: string, tab?: "overview" | "artifacts") => void;
  onCompare?: (runIds: string[]) => void;
  className?: string;
}

/** Server-paginated catalogue of the caller's simulation runs. */
export function AnalyticsLibrary({
  onSelectRun,
  onCompare,
  className = "",
}: AnalyticsLibraryProps = {}): ReactNode {
  const [runs, setRuns] = useState<RunCatalogueEntry[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async (requested: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClients.analyticsWorkbench.listRuns({
        page: requested,
        page_size: LIBRARY_PAGE_SIZE,
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

  const toggleArchive = useCallback(async (entry: RunCatalogueEntry) => {
    setActionError(null);
    try {
      const response = await apiClients.analyticsWorkbench.archiveRun(
        entry.run_id,
        {
          archive_state:
            entry.archive_state === "archived" ? "active" : "archived",
        },
      );
      if (response.status === "error") {
        setActionError(response.error.message);
        return;
      }
      setRuns((current) =>
        current.map((item) =>
          item.run_id === response.data.run_id ? response.data : item,
        ),
      );
    } catch (cause) {
      setActionError(failureMessage(cause));
    }
  }, []);

  return (
    <section
      className={`analytics-library ${className}`.trim()}
      aria-label="Analytics run library"
    >
      <header className="analytics-library__header">
        <h2>Run library</h2>
        <p className="analytics-library__note">
          Archiving changes catalogue metadata only. Immutable simulation
          artifacts are never deleted from this view.
        </p>
      </header>

      {error ? <p role="alert">{error}</p> : null}
      {actionError ? <p role="alert">{actionError}</p> : null}

      {loading ? (
        <p role="status">Loading run catalogue…</p>
      ) : runs.length === 0 ? (
        <p>No runs are recorded for this account yet.</p>
      ) : (
        <table className="analytics-library__table">
          <caption className="sr-only">Simulation run catalogue</caption>
          <thead>
            <tr>
              <th scope="col">Run ID</th>
              <th scope="col">Name</th>
              <th scope="col">Strategy</th>
              <th scope="col">Symbols</th>
              <th scope="col">Timeframe</th>
              <th scope="col">Window</th>
              <th scope="col">Origin</th>
              <th scope="col">Evidence</th>
              <th scope="col">Status</th>
              <th scope="col">Quality</th>
              <th scope="col">Report</th>
              <th scope="col">Created</th>
              <th scope="col">Completed</th>
              <th scope="col">Tags</th>
              <th scope="col">Archive</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((entry) => (
              <tr key={entry.run_id}>
                <td className="font-mono">{entry.run_id}</td>
                <td>{entry.name ?? "—"}</td>
                <td>
                  {entry.strategy_label ?? entry.strategy_id}
                  {entry.strategy_version ? ` (${entry.strategy_version})` : ""}
                </td>
                <td>{entry.symbols.join(", ")}</td>
                <td>{entry.timeframe}</td>
                <td>
                  {toDate(entry.measurement_start)} → {toDate(entry.measurement_end)}
                </td>
                <td>{entry.origin_kind}</td>
                <td>{entry.evidence_class}</td>
                <td>{entry.status}</td>
                <td>{entry.quality_status ?? "—"}</td>
                <td>{entry.report_id ? "attached" : "unavailable"}</td>
                <td>{toDate(entry.created_at)}</td>
                <td>{toDate(entry.completed_at)}</td>
                <td>{entry.tags.length > 0 ? entry.tags.join(", ") : "—"}</td>
                <td>{entry.archive_state}</td>
                <td className="analytics-library__actions">
                  <button
                    type="button"
                    onClick={() => onSelectRun?.(entry.run_id, "overview")}
                    className="text-teal-400 hover:text-teal-300 underline cursor-pointer bg-transparent border-0 p-0 text-xs"
                  >
                    Open
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      onCompare
                        ? onCompare([entry.run_id])
                        : onSelectRun?.(entry.run_id, "overview")
                    }
                    className="text-teal-400 hover:text-teal-300 underline cursor-pointer bg-transparent border-0 p-0 text-xs"
                  >
                    Compare
                  </button>
                  <button
                    type="button"
                    onClick={() => onSelectRun?.(entry.run_id, "artifacts")}
                    className="text-teal-400 hover:text-teal-300 underline cursor-pointer bg-transparent border-0 p-0 text-xs"
                  >
                    Artifacts
                  </button>
                  <button
                    type="button"
                    onClick={() => void toggleArchive(entry)}
                    className="text-slate-400 hover:text-slate-300 underline cursor-pointer bg-transparent border-0 p-0 text-xs"
                  >
                    {entry.archive_state === "archived" ? "Unarchive" : "Archive"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <nav className="analytics-library__pager" aria-label="Run catalogue pages">
        <button
          type="button"
          onClick={() => setPage((current) => Math.max(1, current - 1))}
          disabled={page <= 1 || loading}
        >
          Previous page
        </button>
        <span>Page {page}</span>
        <button
          type="button"
          onClick={() => setPage((current) => current + 1)}
          disabled={loading || runs.length < LIBRARY_PAGE_SIZE}
        >
          Next page
        </button>
      </nav>
    </section>
  );
}
