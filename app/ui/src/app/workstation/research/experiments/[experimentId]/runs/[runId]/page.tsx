/**
 * Run route (FEAT-UI-28).
 *
 * A run without an explicit stage segment redirects to its overview, so every
 * workbench URL identifies experiment, run, and stage.
 */

"use client";

import { useRouter } from "next/navigation";
import { use, useEffect, type ReactNode } from "react";

export default function Page({
  params,
}: {
  params: Promise<{ experimentId: string; runId: string }>;
}): ReactNode {
  const { experimentId, runId } = use(params);
  const router = useRouter();
  useEffect(() => {
    router.replace(
      `/workstation/research/experiments/${experimentId}/runs/${runId}/overview`
    );
  }, [router, experimentId, runId]);
  return <p className="research-note">Opening run overview…</p>;
}
