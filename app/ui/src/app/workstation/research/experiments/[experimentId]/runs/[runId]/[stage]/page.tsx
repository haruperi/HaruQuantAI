/**
 * Run stage route (FEAT-UI-28).
 *
 * The route segment is the navigation state: refresh-safe, shareable, and
 * independently loadable. The stage panel is chosen by the workbench shell.
 */

"use client";

import { notFound } from "next/navigation";
import { use, type ReactNode } from "react";

import {
  EvidenceGate,
  ResearchWorkbench,
  isStageView,
  useExperiment,
  useRun,
} from "@/features/research";

export default function Page({
  params,
}: {
  params: Promise<{ experimentId: string; runId: string; stage: string }>;
}): ReactNode {
  const { experimentId, runId, stage } = use(params);
  const run = useRun(runId);
  const experiment = useExperiment(experimentId);

  if (!isStageView(stage)) {
    notFound();
  }

  return (
    <EvidenceGate
      loading={run.loading && run.data === null}
      error={run.error}
      reload={run.reload}
      ready={run.data !== null}
      loadingLabel="Loading run…"
    >
      {run.data ? (
        <ResearchWorkbench
          detail={run.data}
          experimentId={experimentId}
          experimentName={experiment.data?.name}
          stage={stage}
          onChanged={run.reload}
        />
      ) : null}
    </EvidenceGate>
  );
}
