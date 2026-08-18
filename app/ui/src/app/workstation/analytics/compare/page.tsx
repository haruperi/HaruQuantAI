/**
 * Analytics comparison route (FEAT-UI-32).
 *
 * Compares 2 or more simulation runs using Analytics-owned multi-run evidence.
 */

"use client";

import { Suspense, useMemo, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { Layers } from "lucide-react";

import { ProtectedLayout } from "@/app/protected-layout";
import { AnalyticsWorkspace } from "@/features/analytics-workbench";

function AnalyticsCompareContent(): ReactNode {
  const searchParams = useSearchParams();
  const runsParam = searchParams?.get("runs") ?? "";
  const runIds = useMemo(() => {
    return runsParam
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);
  }, [runsParam]);

  return (
    <AnalyticsWorkspace compareRunIds={runIds}>
      <div className="flex flex-col items-center justify-center p-12 text-center gap-4">
        <div className="p-3 rounded-full bg-slate-800/80 border border-slate-700/60">
          <Layers className="w-8 h-8 text-teal-400" aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-white">Multi-Run Comparison</h2>
        {runIds.length > 0 ? (
          <p className="text-sm text-slate-400 font-mono">
            Comparing {runIds.length} run{runIds.length === 1 ? "" : "s"}: {runIds.join(", ")}
          </p>
        ) : (
          <p className="text-sm text-slate-400">
            No run IDs selected. Add runs via query parameter (e.g. ?runs=run1,run2).
          </p>
        )}
      </div>
    </AnalyticsWorkspace>
  );
}

export default function AnalyticsComparePage(): ReactNode {
  return (
    <ProtectedLayout>
      <Suspense fallback={null}>
        <AnalyticsCompareContent />
      </Suspense>
    </ProtectedLayout>
  );
}
