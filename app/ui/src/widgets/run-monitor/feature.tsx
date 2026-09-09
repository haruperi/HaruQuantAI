"use client";

import React from "react";

import { RUN_MONITOR_MANIFEST } from "./manifest";
import {
  boundedRows,
  controlLabel,
  outcomeLabel,
  progressLabel,
  type RunMonitorRow,
} from "./model";

export interface RunMonitorAdapter {
  readonly rows: readonly RunMonitorRow[];
  readonly unavailableReason?: string | null;
  requestControl(jobId: string, control: "CANCEL" | "PAUSE" | "RESUME"): Promise<void>;
}

export interface RunMonitorFeatureProps {
  readonly adapter?: RunMonitorAdapter;
}

/** Render only current owner projections; absent adapter fails visibly closed. */
export function RunMonitorFeature({ adapter }: RunMonitorFeatureProps): React.JSX.Element {
  if (adapter === undefined) {
    return (
      <section role="status" aria-label={RUN_MONITOR_MANIFEST.title}>
        <h2>{RUN_MONITOR_MANIFEST.title}</h2>
        <p>Job monitoring is unavailable because interfaces.operate-jobs@1 is not bound.</p>
      </section>
    );
  }
  if (adapter.unavailableReason) {
    return <section role="status">Jobs unavailable: {adapter.unavailableReason}</section>;
  }
  const rows = boundedRows(adapter.rows);
  return (
    <section aria-label={RUN_MONITOR_MANIFEST.title}>
      <h2>{RUN_MONITOR_MANIFEST.title}</h2>
      {adapter.rows.length > rows.length && (
        <p role="status">Showing the first {rows.length} jobs from a bounded projection.</p>
      )}
      <ul>
        {rows.map((row) => {
          const progress = progressLabel(row);
          return (
            <li key={`${row.jobId}:${row.attemptId}:${row.fence}`} aria-label={`Job ${row.jobId}`}>
              <strong>{row.jobId}</strong>
              <div>Infrastructure: {row.infrastructureState}</div>
              <div>{outcomeLabel(row)}</div>
              <div>{controlLabel(row)}</div>
              <div>{row.workerActive ? "Worker active" : "No worker allocated"}</div>
              <div aria-label="Progress">{progress.text}</div>
              {row.stale && <div role="status">Stale projection; current result not asserted.</div>}
              <button type="button" onClick={() => void adapter.requestControl(row.jobId, "CANCEL")}>Cancel</button>
              <button type="button" onClick={() => void adapter.requestControl(row.jobId, "PAUSE")}>Pause</button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
