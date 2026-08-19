/**
 * Analytics comparison route (FEAT-UI-32).
 *
 * Compares 2 or more simulation runs using Analytics-owned multi-run evidence.
 */

"use client";

import { Suspense, useMemo, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";

import { ProtectedLayout } from "@/app/protected-layout";
import {
  AnalyticsComparison,
  AnalyticsWorkspace,
} from "@/features/analytics-workbench";

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
      <AnalyticsComparison initialRunIds={runIds} />
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
