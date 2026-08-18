/** New experiment / run builder route (FEAT-UI-28). */

"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, type ReactNode } from "react";

import { ResearchRunBuilder } from "@/features/research";

/** Reads the prefill parameters a "Rerun" link carries. */
function Builder(): ReactNode {
  const params = useSearchParams();
  return (
    <ResearchRunBuilder
      initialExperimentId={params.get("experiment") ?? undefined}
      initialSymbol={params.get("symbol") ?? undefined}
      initialTimeframe={params.get("timeframe") ?? undefined}
      initialPreset={params.get("preset") ?? undefined}
    />
  );
}

export default function Page(): ReactNode {
  return (
    <Suspense fallback={<p className="research-note">Loading run builder…</p>}>
      <Builder />
    </Suspense>
  );
}
