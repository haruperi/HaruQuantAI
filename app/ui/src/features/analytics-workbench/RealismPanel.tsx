/**
 * Simulation realism evidence panel (FEAT-UI-32).
 *
 * Realism context lives on an Analytics screen because analytics without it can
 * mislead, but every value here is Simulation-owned. The panel reads the
 * canonical Simulation result and renders its realism and diagnostics blocks
 * verbatim: nothing is summarised, scored, or recomputed.
 */

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";

/** Ordered realism blocks exactly as the realism screen specifies. */
export const REALISM_BLOCKS: readonly (readonly [string, string])[] = [
  ["tick_model", "Tick model"],
  ["slippage", "Slippage"],
  ["liquidity", "Liquidity"],
  ["sessions", "Sessions"],
  ["data_quality", "Data quality"],
  ["assumptions", "Assumptions"],
  ["limitations", "Limitations"],
  ["calibration", "Calibration"],
  ["parity", "Parity and certification target"],
  ["fault_scenarios", "Fault scenarios"],
];

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The canonical Simulation result is unavailable.";
}

/** Render one owner block as a list, a definition grid, or a scalar. */
function OwnerBlock({ value }: { value: unknown }): ReactNode {
  if (value === null || value === undefined || value === "") {
    return <p className="analytics-evidence__unavailable">Unavailable</p>;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <p className="analytics-evidence__unavailable">Unavailable</p>;
    }
    return (
      <ul>
        {value.map((entry, index) => (
          <li key={`${String(entry)}-${index}`}>
            {typeof entry === "object" ? JSON.stringify(entry) : String(entry)}
          </li>
        ))}
      </ul>
    );
  }
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    if (entries.length === 0) {
      return <p className="analytics-evidence__unavailable">Unavailable</p>;
    }
    return (
      <dl className="analytics-realism__grid">
        {entries.map(([key, entry]) => (
          <div key={key} className="analytics-realism__row">
            <dt>{key}</dt>
            <dd>
              {typeof entry === "object" && entry !== null
                ? JSON.stringify(entry)
                : String(entry)}
            </dd>
          </div>
        ))}
      </dl>
    );
  }
  return <p>{String(value)}</p>;
}

/** Props accepted by `RealismPanel`. */
export interface RealismPanelProps {
  runId: string;
  className?: string;
}

/** Simulation-owned realism and diagnostics evidence for one run. */
export function RealismPanel({
  runId,
  className = "",
}: RealismPanelProps): ReactNode {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response =
        await apiClients.analyticsWorkbench.getSimulationResult(runId);
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setResult(response.data);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void load();
  }, [load]);

  const realism = (result?.realism ?? {}) as Record<string, unknown>;
  const diagnostics = result?.diagnostics;

  return (
    <section
      className={`analytics-realism ${className}`.trim()}
      aria-label="Simulation realism evidence"
    >
      <h3>Realism</h3>
      <p className="analytics-realism__note">
        This evidence is Simulation-owned. Analytics presents it unchanged so
        performance figures are read with their execution context.
      </p>

      {loading ? <p role="status">Loading realism evidence…</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      {result ? (
        <>
          {REALISM_BLOCKS.map(([key, label]) => (
            <section key={key} aria-labelledby={`realism-${key}`}>
              <h4 id={`realism-${key}`}>{label}</h4>
              <OwnerBlock value={realism[key]} />
            </section>
          ))}

          <section aria-labelledby="realism-diagnostics">
            <h4 id="realism-diagnostics">Diagnostics</h4>
            <OwnerBlock value={diagnostics} />
          </section>
        </>
      ) : null}
    </section>
  );
}
