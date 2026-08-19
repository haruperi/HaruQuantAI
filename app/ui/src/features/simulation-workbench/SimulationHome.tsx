/**
 * Simulation workbench routing shell (FEAT-UI-31).
 *
 * Owns mode selection and delegates to the mode-specific workbench pane. A
 * successful builder submission hands off to the matching authoritative
 * monitor; no run or batch outcome is ever inferred locally.
 */

"use client";

import { useCallback, useState, type ReactNode } from "react";

import type { LiveSessionProjection } from "@/clients";

import { SimulationWorkbench } from "./SimulationWorkbench";
import type { SimulationMode } from "./SimulationWorkbench";
import { SimulationRunBuilder } from "./SimulationRunBuilder";
import type { RunBuilderSubmission } from "./SimulationRunBuilder";
import { CanonicalRunMonitor } from "./CanonicalRunMonitor";
import { BatchRunMonitor } from "./BatchRunMonitor";
import { RunCataloguePanel } from "./RunCataloguePanel";
import { InteractiveSimulationWorkspace } from "./InteractiveSimulationWorkspace";
import { SessionStatePanels } from "./SessionStatePanels";
import { ManualCommandPanel } from "./ManualCommandPanel";
import { WhatIfPanel } from "./WhatIfPanel";
import { SimulationRecoveryPanel } from "./SimulationRecoveryPanel";
import { SimulationFinalizeDialog } from "./SimulationFinalizeDialog";
import { ScenarioPanel, type ScenarioEvidence } from "./ScenarioPanel";
import { ChecklistPanel, type ChecklistEvidence } from "./ChecklistPanel";
import { MissionPanel, type MissionOutcomeEvidence } from "./MissionPanel";

/**
 * Read one optional owner evidence block from a session projection.
 *
 * Scenario, checklist, and mission evidence is Simulator-owned and only
 * present on sessions the owner runs as a mission. Reading it defensively lets
 * the panels say plainly that nothing was supplied instead of implying an
 * empty scenario is a scenario with nothing in it.
 */
function ownerEvidence<T>(
  session: LiveSessionProjection | null,
  key: string,
): T | null {
  const value = (session as Record<string, unknown> | null)?.[key];
  return value && typeof value === "object" ? (value as T) : null;
}

/** Route-provided context passed into the workbench home. */
export interface SimulationHomeProps {
  initialMode?: SimulationMode;
  initialRunId?: string;
  initialSessionId?: string;
  initialBatchId?: string;
  className?: string;
}

/**
 * Live practice pane for one interactive session.
 *
 * The workspace owns pacing and authoritative reads; the docked panels render
 * the state it reports. Session state is held here so a command receipt and a
 * recovery transition refresh every panel from the same server truth.
 */
function PracticeMonitor({ sessionId }: { sessionId?: string }): ReactNode {
  const [session, setSession] = useState<LiveSessionProjection | null>(null);

  if (!sessionId) {
    return (
      <section>
        <h3>Live practice</h3>
        <p>No practice session identifier was provided.</p>
      </section>
    );
  }

  return (
    <InteractiveSimulationWorkspace
      sessionId={sessionId}
      onSessionChange={setSession}
    >
      <SessionStatePanels session={session} />
      <ManualCommandPanel
        sessionId={sessionId}
        session={session}
        onSessionRefreshed={setSession}
      />
      <WhatIfPanel sessionId={sessionId} session={session} />
      <ScenarioPanel scenario={ownerEvidence<ScenarioEvidence>(session, "scenario")} />
      <ChecklistPanel
        checklist={ownerEvidence<ChecklistEvidence>(session, "checklist")}
      />
      <MissionPanel
        outcome={ownerEvidence<MissionOutcomeEvidence>(session, "mission_outcome")}
      />
      <SimulationRecoveryPanel
        sessionId={sessionId}
        session={session}
        onSessionChanged={setSession}
      />
      <SimulationFinalizeDialog
        sessionId={sessionId}
        session={session}
        onSessionChanged={setSession}
      />
    </InteractiveSimulationWorkspace>
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
    return <RunCataloguePanel />;
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
