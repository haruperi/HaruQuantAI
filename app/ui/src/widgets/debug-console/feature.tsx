"use client";

import React, { useMemo, useState } from "react";

import { DEBUG_CONSOLE_MANIFEST } from "./manifest";
import {
  boundedDiagnosticWindow,
  diagnosticText,
  type DiagnosticLogEntry,
} from "./model";

export interface DebugConsoleAdapter {
  readonly authorized: boolean;
  readonly enabled: boolean;
  readonly unavailableReason?: string | null;
  readonly entries: readonly DiagnosticLogEntry[];
}

export interface DebugConsoleFeatureProps {
  readonly adapter?: DebugConsoleAdapter;
}

/** Render only redacted public diagnostics and keep Clear local to the viewport. */
export function DebugConsoleFeature({ adapter }: DebugConsoleFeatureProps): React.JSX.Element {
  const [clearedThrough, setClearedThrough] = useState(0);
  const windowed = useMemo(
    () => boundedDiagnosticWindow(adapter?.entries ?? []),
    [adapter?.entries],
  );

  if (adapter === undefined || adapter.unavailableReason) {
    return (
      <section role="status" aria-label={DEBUG_CONSOLE_MANIFEST.title}>
        Debug Console unavailable{adapter?.unavailableReason ? `: ${adapter.unavailableReason}` : "."}
      </section>
    );
  }
  if (!adapter.enabled || !adapter.authorized) {
    return <section role="status">Debug Console is disabled or unauthorized.</section>;
  }

  const visible = windowed.entries.filter((entry) => entry.sequence > clearedThrough);
  return (
    <section aria-label={DEBUG_CONSOLE_MANIFEST.title}>
      <header>
        <h2>{DEBUG_CONSOLE_MANIFEST.title}</h2>
        <button
          type="button"
          onClick={() =>
            setClearedThrough(windowed.entries.at(-1)?.sequence ?? clearedThrough)
          }
        >
          Clear display
        </button>
      </header>
      {windowed.truncated && <p role="status">Older diagnostics are outside this bounded window.</p>}
      <ol>
        {visible.map((entry) => (
          <li key={entry.sequence}>
            <time>{entry.timestamp}</time>{" "}
            <strong>{entry.owner}</strong>{" "}
            <span>{entry.severity}</span>{" "}
            <code>{entry.code}</code>{" "}
            <span>{diagnosticText(entry.message)}</span>{" "}
            {entry.sampled && <em>(sampled)</em>}
          </li>
        ))}
      </ol>
    </section>
  );
}
