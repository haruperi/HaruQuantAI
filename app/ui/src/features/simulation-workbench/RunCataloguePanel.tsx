/**
 * Historical run catalogue pane (FEAT-UI-31).
 *
 * Lists the caller's recorded simulation runs, newest first, and hands each
 * one off to the Analytics workspace. Every value shown is server evidence:
 * the panel never derives a status, a metric, or an outcome of its own.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";

import { ApiClientError, apiClients, type RunCatalogueEntry } from "@/clients";

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
  className?: string;
}

/** Server-paginated catalogue of the caller's recorded simulation runs. */
export function RunCataloguePanel({
  className = "",
}: RunCataloguePanelProps = {}): ReactNode {
  const [runs, setRuns] = useState<RunCatalogueEntry[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    <section className={className} aria-label="Run catalogue">
      <h3>Run catalogue</h3>
      {error ? (
        <p role="alert">{error}</p>
      ) : loading ? (
        <p>Loading recorded runs…</p>
      ) : runs.length === 0 ? (
        <p>No runs have been recorded yet.</p>
      ) : (
        <table>
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
                <td>{entry.run_id}</td>
                <td>{entry.strategy_label ?? entry.strategy_id}</td>
                <td>{entry.symbols.join(", ")}</td>
                <td>
                  {toDate(entry.measurement_start)} → {toDate(entry.measurement_end)}
                </td>
                <td>{entry.origin_kind}</td>
                <td>{entry.status}</td>
                <td>{entry.evidence_class}</td>
                <td>
                  <Link
                    href={`/workstation/analytics/${encodeURIComponent(entry.run_id)}/overview`}
                  >
                    Open in Analytics
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <nav aria-label="Run catalogue pages">
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
