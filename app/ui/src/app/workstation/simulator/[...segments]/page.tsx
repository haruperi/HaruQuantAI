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
 * - /workstation/simulator/replay/[runId] -> immutable journal playback
 */

"use client";

import { use, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";

import { ProtectedLayout } from "@/app/protected-layout";
import {
  SimulationHome,
  SimulationPlaybackWorkspace,
  type SimulationMode,
} from "@/features/simulation-workbench";

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
  const searchParams = useSearchParams();

  if (first === "replay" && second) {
    return (
      <ProtectedLayout>
        <SimulationPlaybackWorkspace
          runId={second}
          ticket={searchParams?.get("ticket") ?? undefined}
          returnHref={searchParams?.get("return") ?? undefined}
        />
      </ProtectedLayout>
    );
  }

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
      <SimulationHome
        initialMode={mode}
        initialRunId={runId}
        initialSessionId={sessionId}
        initialBatchId={batchId}
      />
    </ProtectedLayout>
  );
}
