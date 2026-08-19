/**
 * Simulation workbench routing shell (FEAT-UI-31).
 *
 * Owns mode selection and delegates to the mode-specific workbench pane. A
 * successful builder submission hands off to the matching authoritative
 * monitor; no run or batch outcome is ever inferred locally.
 */

"use client";

import { useCallback, useState, type ReactNode } from "react";

import { SimulationWorkbench } from "./SimulationWorkbench";
import type { SimulationMode } from "./SimulationWorkbench";
import { SimulationRunBuilder } from "./SimulationRunBuilder";
import type { RunBuilderSubmission } from "./SimulationRunBuilder";
import { CanonicalRunMonitor } from "./CanonicalRunMonitor";
import { BatchRunMonitor } from "./BatchRunMonitor";

/** Route-provided context passed into the workbench home. */
export interface SimulationHomeProps {
  initialMode?: SimulationMode;
  initialRunId?: string;
  initialSessionId?: string;
  initialBatchId?: string;
  className?: string;
}

/** Small placeholder for unimplemented modes while keeping route behavior explicit. */
function PracticeMonitor({ sessionId }: { sessionId?: string }): ReactNode {
  return (
    <section>
      <h3>Live practice</h3>
      <p>Practice mode is currently in staged rollout.</p>
      {sessionId ? <p>Active session: {sessionId}</p> : null}
    </section>
  );
}

/** Small placeholder for historical catalogue mode while still validating tab state. */
function HistoryMonitor(): ReactNode {
  return (
    <section>
      <h3>Run catalogue</h3>
      <p>Run evidence catalogue is in staged rollout.</p>
    </section>
  );
}

/** Route-aware workbench shell with mode-specific render panels. */
export function SimulationHome({
  initialMode = "canonical",
  initialRunId,
  initialSessionId,
  initialBatchId,
  className,
}: SimulationHomeProps): ReactNode {
  const [activeMode, setActiveMode] = useState<SimulationMode>(initialMode);
  const [runId, setRunId] = useState<string | undefined>(initialRunId);
  const [batchId, setBatchId] = useState<string | undefined>(initialBatchId);

  const handleSubmitted = useCallback((submission: RunBuilderSubmission) => {
    if (submission.kind === "run") {
      setRunId(submission.runId);
      setActiveMode("canonical");
      return;
    }
    setBatchId(submission.batchId);
    setActiveMode("batch");
  }, []);

  const panel = ((): ReactNode => {
    if (activeMode === "canonical") {
      if (runId) return <CanonicalRunMonitor runId={runId} />;
      return (
        <SimulationRunBuilder
          initialMode="canonical_backtest"
          onSubmitted={handleSubmitted}
        />
      );
    }
    if (activeMode === "batch") {
      if (batchId) return <BatchRunMonitor batchId={batchId} />;
      return (
        <SimulationRunBuilder initialMode="batch" onSubmitted={handleSubmitted} />
      );
    }
    if (activeMode === "practice") {
      return <PracticeMonitor sessionId={initialSessionId} />;
    }
    return <HistoryMonitor />;
  })();

  return (
    <SimulationWorkbench
      initialMode={activeMode}
      className={className}
      onModeChange={setActiveMode}
    >
      {panel}
    </SimulationWorkbench>
  );
}
