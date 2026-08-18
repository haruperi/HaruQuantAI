/**
 * Simulator catch-all sub-routes (FEAT-UI-31).
 *
 * Routes supported:
 * - /workstation/simulator/practice -> practice mode
 * - /workstation/simulator/practice/[sessionId] -> practice mode with active session
 * - /workstation/simulator/batch -> batch grid mode
 * - /workstation/simulator/batch/[batchId] -> batch grid mode with active batch
 * - /workstation/simulator/history -> run catalogue mode
 * - /workstation/simulator/runs/[runId] -> canonical mode with active run
 */

"use client";

import { use, type ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import {
  SimulationWorkbench,
  type SimulationMode,
} from "@/features/simulation-workbench";
import { SimulatorWidget } from "@/features/simulator";

export interface SimulatorSegmentsPageProps {
  params: { segments?: string[] } | Promise<{ segments?: string[] }>;
}

export default function SimulatorSegmentsPage({
  params,
}: SimulatorSegmentsPageProps): ReactNode {
  const isPromise = params && typeof (params as Promise<unknown>).then === "function";
  const resolved = isPromise
    ? use(params as Promise<{ segments?: string[] }>)
    : (params as { segments?: string[] });
  const segments = resolved?.segments ?? [];

  const first = segments[0]?.toLowerCase() ?? "";
  const second = segments[1];

  let mode: SimulationMode = "canonical";
  let runId: string | undefined;
  let sessionId: string | undefined;
  let batchId: string | undefined;

  if (first === "practice") {
    mode = "practice";
    sessionId = second;
  } else if (first === "batch") {
    mode = "batch";
    batchId = second;
  } else if (first === "history") {
    mode = "history";
  } else if (first === "runs") {
    mode = "canonical";
    runId = second;
  }

  return (
    <ProtectedLayout>
      <SimulationWorkbench
        initialMode={mode}
        initialRunId={runId}
        initialSessionId={sessionId}
        initialBatchId={batchId}
      >
        {mode === "canonical" && !runId ? <SimulatorWidget /> : undefined}
      </SimulationWorkbench>
    </ProtectedLayout>
  );
}
