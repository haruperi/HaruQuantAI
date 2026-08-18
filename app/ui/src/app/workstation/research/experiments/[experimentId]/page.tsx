/** One experiment and its run history (FEAT-UI-28). */

"use client";

import { use, type ReactNode } from "react";

import { ResearchExperimentDetailView } from "@/features/research";

export default function Page({
  params,
}: {
  params: Promise<{ experimentId: string }>;
}): ReactNode {
  const { experimentId } = use(params);
  return <ResearchExperimentDetailView experimentId={experimentId} />;
}
