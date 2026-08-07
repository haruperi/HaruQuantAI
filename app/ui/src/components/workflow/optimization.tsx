/** Advisory Optimization workflow presentation. */

"use client";

import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { OptimizationRecord } from "@/clients";

/** Props accepted by `OptimizationView`. */
export interface OptimizationViewProps {
  className?: string;
}

const DEFAULT_REQUEST = JSON.stringify(
  {
    method: "grid",
    max_candidates: 10,
    seed: 42,
  },
  null,
  2
);

/** Run one bounded request and present advisory evidence only. */
export function OptimizationView({ className }: OptimizationViewProps = {}): ReactNode {
  const [requestText, setRequestText] = useState(DEFAULT_REQUEST);
  const [result, setResult] = useState<OptimizationRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSweep(): Promise<void> {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = JSON.parse(requestText) as Record<string, unknown>;
      const response = await apiClients.optimization.parameterSweep(payload);
      if (response.status === "error") setError(response.error.message);
      else setResult(response.data);
    } catch (cause) {
      if (cause instanceof SyntaxError) setError("Request must be valid JSON");
      else setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={`workflow-optimization ${className ?? ""}`.trim()}
      role="region"
      aria-label="Optimization"
    >
      <p>
        Advisory only. Optimization cannot place trades or adopt Strategy parameters.
      </p>
      <label>
        Bounded parameter sweep request
        <textarea
          aria-label="Bounded parameter sweep request"
          value={requestText}
          onChange={(event) => setRequestText(event.target.value)}
          rows={8}
        />
      </label>
      <button type="button" onClick={() => void runSweep()} disabled={loading}>
        Run bounded optimization
      </button>
      {loading && <span role="status">running…</span>}
      {error && <span className="workflow-error" role="alert">{error}</span>}
      {result && (
        <section aria-label="Advisory optimization result">
          <h4>Advisory result</h4>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}
