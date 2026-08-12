/**
 * Simulation backtest presentation (FR-UI-013).
 *
 * Two modes: run a synchronous backtest (`simulation.run`) and render the
 * result, or look up a stored result by run id (`simulation.result`). No
 * metrics are invented; only fields present in the opaque `SimulationResult`
 * payload are rendered defensively.
 */

"use client";

import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { SimulationResult } from "@/clients";

/** Props accepted by `SimulationView`. */
export interface SimulationViewProps {
  className?: string;
}

/** Read-only field accessor for an opaque result payload. */
function field(result: SimulationResult, key: string): string {
  const value = result[key];
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/** Simulation run + result-lookup view. */
export function SimulationView({ className }: SimulationViewProps = {}): ReactNode {
  const [hypothesis, setHypothesis] = useState("");
  const [symbol, setSymbol] = useState("EURUSD");
  const [runId, setRunId] = useState("");
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runBacktest(): Promise<void> {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await apiClients.simulation.run({
        hypothesis,
        dataset: { symbol },
      });
      if (response.status === "error") {
        setError(response.error.message);
      } else {
        setResult(response.data);
      }
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setLoading(false);
    }
  }

  async function lookupResult(): Promise<void> {
    if (!runId.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await apiClients.simulation.result(runId.trim());
      if (response.status === "error") {
        setError(response.error.message);
      } else {
        setResult(response.data);
      }
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`workflow-simulation ${className ?? ""}`.trim()} role="region" aria-label="Simulation">
      <div className="workflow-sim-controls">
        <label>
          Symbol
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} />
        </label>
        <label>
          Hypothesis
          <input value={hypothesis} onChange={(e) => setHypothesis(e.target.value)} />
        </label>
        <button type="button" onClick={() => void runBacktest()} disabled={loading}>
          Run Backtest
        </button>
        <label>
          Run ID
          <input value={runId} onChange={(e) => setRunId(e.target.value)} />
        </label>
        <button type="button" onClick={() => void lookupResult()} disabled={loading || !runId.trim()}>
          Look Up
        </button>
      </div>

      {loading && <span>running…</span>}
      {error && <span className="workflow-error">{error}</span>}
      {result && (
        <div className="workflow-sim-result">
          <div className="workflow-sim-field"><strong>Run ID:</strong> {field(result, "run_id")}</div>
          <div className="workflow-sim-field"><strong>Status:</strong> {field(result, "status")}</div>
          <div className="workflow-sim-field"><strong>Request hash:</strong> {field(result, "request_hash")}</div>
          <div className="workflow-sim-field"><strong>Config hash:</strong> {field(result, "config_hash")}</div>
          <div className="workflow-sim-field"><strong>Engine:</strong> {field(result, "engine_version")}</div>
          <div className="workflow-sim-field"><strong>Initial balance:</strong> {field(result, "initial_balance")}</div>
          <details>
            <summary>Full result</summary>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}
