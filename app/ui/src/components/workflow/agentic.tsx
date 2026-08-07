/** Governed Agentic operator workflow presentation. */

"use client";

import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { AgenticRecord } from "@/clients/agentic";
import type { ApiResponse } from "@/clients/contracts";

/** Props accepted by `AgenticView`. */
export interface AgenticViewProps {
  className?: string;
}

/** Reserve, inspect, and contain Agentic work without granting trading authority. */
export function AgenticView({ className }: AgenticViewProps = {}): ReactNode {
  const [workflowName, setWorkflowName] = useState("firm_research_council");
  const [objective, setObjective] = useState("Assess governed EURUSD evidence.");
  const [runId, setRunId] = useState("");
  const [taskId, setTaskId] = useState("");
  const [result, setResult] = useState<AgenticRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function invoke(
    operation: () => Promise<ApiResponse<AgenticRecord>>
  ): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const response = await operation();
      if (response.status === "error") setError(response.error.message);
      else setResult(response.data);
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={`workflow-agentic ${className ?? ""}`.trim()}
      role="region"
      aria-label="Agentic operator"
    >
      <p>
        Agentic reserves research work and submits untrusted proposals. It cannot
        approve risk, clear deterministic kill switches, or execute trades.
      </p>
      <label>
        Workflow
        <input value={workflowName} onChange={(event) => setWorkflowName(event.target.value)} />
      </label>
      <label>
        Bounded objective
        <textarea
          aria-label="Bounded objective"
          value={objective}
          onChange={(event) => setObjective(event.target.value)}
        />
      </label>
      <button
        type="button"
        disabled={loading || !workflowName.trim() || !objective.trim()}
        onClick={() => void invoke(() => apiClients.agentic.submitRun({
          workflow_name: workflowName,
          objective,
          input_refs: [],
          deadline_seconds: 1800,
        }))}
      >
        Reserve Agentic run
      </button>
      <label>
        Run ID
        <input value={runId} onChange={(event) => setRunId(event.target.value)} />
      </label>
      <label>
        Task ID for audit
        <input value={taskId} onChange={(event) => setTaskId(event.target.value)} />
      </label>
      <button type="button" disabled={loading || !runId} onClick={() => void invoke(() => apiClients.agentic.getRun(runId))}>
        Inspect run
      </button>
      <button type="button" disabled={loading || !runId || !taskId} onClick={() => void invoke(() => apiClients.agentic.runAudit(runId, taskId))}>
        Read redacted audit
      </button>
      <button
        type="button"
        disabled={loading || !runId}
        onClick={() => {
          if (window.confirm("Cancel this Agentic run? This grants no trading authority.")) {
            void invoke(() => apiClients.agentic.cancelRun(runId));
          }
        }}
      >
        Cancel run
      </button>
      <button
        type="button"
        disabled={loading}
        onClick={() => {
          if (window.confirm("Disable new Agentic work and drain active runs?")) {
            void invoke(() => apiClients.agentic.disable({ run_ids: [], policy: "drain" }));
          }
        }}
      >
        Disable Agentic
      </button>
      {loading && <span role="status">working…</span>}
      {error && <span role="alert">{error}</span>}
      {result && <pre aria-label="Agentic result">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
