/**
 * Core Edge Lab research presentation (FR-UI-016).
 *
 * Runs an Edge Lab profile via the typed client and renders the advisory
 * `ResearchReport`. Research-internal profile/scorecard/snapshot sub-views are
 * explicitly absent — only the registered report evidence is rendered.
 */

"use client";

import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { ResearchReport } from "@/clients";

/** Props accepted by `ResearchWorkspace`. */
export interface ResearchWorkspaceProps {
  className?: string;
}

/** Edge Lab research workspace. */
export function ResearchWorkspace({ className }: ResearchWorkspaceProps = {}): ReactNode {
  const [hypothesis, setHypothesis] = useState("");
  const [symbol, setSymbol] = useState("EURUSD");
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runResearch(): Promise<void> {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const response = await apiClients.research.run({
        hypothesis: hypothesis || "default momentum hypothesis",
        dataset: { symbol },
        config: {},
      });
      if (response.status === "error") {
        setError(response.error.message);
      } else {
        setReport(response.data);
      }
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`workflow-research ${className ?? ""}`.trim()} role="region" aria-label="Edge Lab">
      <div className="workflow-research-controls">
        <label>
          Symbol
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} />
        </label>
        <label>
          Hypothesis
          <input value={hypothesis} onChange={(e) => setHypothesis(e.target.value)} />
        </label>
        <button type="button" onClick={() => void runResearch()} disabled={loading}>
          Run Edge Lab
        </button>
      </div>
      {loading && <span>running…</span>}
      {error && <span className="workflow-error">{error}</span>}
      {report && (
        <div className="workflow-research-report">
          <h4>Advisory Report</h4>
          <pre>{JSON.stringify(report, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
