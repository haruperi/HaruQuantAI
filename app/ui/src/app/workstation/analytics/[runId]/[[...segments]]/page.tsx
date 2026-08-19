/**
 * Run-specific Analytics route (FEAT-UI-32).
 *
 * Routes supported:
 * - /workstation/analytics/[runId] -> overview tab
 * - /workstation/analytics/[runId]/overview -> overview tab
 * - /workstation/analytics/[runId]/returns -> returns tab
 * - /workstation/analytics/[runId]/drawdown -> drawdown tab
 * - /workstation/analytics/[runId]/trades -> trades tab
 * - /workstation/analytics/[runId]/trades/[ticket] -> one trade detail
 * - /workstation/analytics/[runId]/grouped -> grouped tab
 * - /workstation/analytics/[runId]/benchmark -> benchmark tab
 * - /workstation/analytics/[runId]/artifacts -> artifacts tab
 *
 * Period dimension and source context travel as query parameters on the
 * grouped tab rather than as routes of their own.
 */

"use client";

import { use, useCallback, useEffect, useState, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";

import { ProtectedLayout } from "@/app/protected-layout";
import { apiClients, type AnalyticsWorkbenchPayload } from "@/clients";
import {
  AnalyticsArtifactDrawer,
  AnalyticsWorkspace,
  BenchmarkPanel,
  ChartsPanel,
  DistributionPanel,
  OverviewPanel,
  PeriodsPanel,
  ProvenancePanel,
  RealismPanel,
  ReturnsPanel,
  RiskPanel,
  TradeDetailPanel,
  TradesPanel,
  type AnalyticsTab,
  type PeriodContext,
} from "@/features/analytics-workbench";
import type { PeriodDimension } from "@/clients";

export interface AnalyticsRunPageProps {
  params:
    | { runId: string; segments?: string[] }
    | Promise<{ runId: string; segments?: string[] }>;
}

const VALID_TABS = new Set<AnalyticsTab>([
  "overview",
  "returns",
  "drawdown",
  "trades",
  "grouped",
  "benchmark",
  "artifacts",
]);

/** Read the owner workbench projection once per run for the payload tabs. */
function useWorkbenchPayload(
  runId: string,
  enabled: boolean,
): { payload: AnalyticsWorkbenchPayload | null; loading: boolean; error: string | null } {
  const [payload, setPayload] = useState<AnalyticsWorkbenchPayload | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    const response =
      await apiClients.analyticsWorkbench.getWorkbenchPayload(runId);
    if (response.status === "error") {
      setError(response.error.message);
    } else {
      setPayload(response.data);
    }
    setLoading(false);
  }, [runId, enabled]);

  useEffect(() => {
    void load();
  }, [load]);

  return { payload, loading, error };
}

export default function AnalyticsRunPage({
  params,
}: AnalyticsRunPageProps): ReactNode {
  const isPromise = params && typeof (params as Promise<unknown>).then === "function";
  const resolved = isPromise
    ? use(params as Promise<{ runId: string; segments?: string[] }>)
    : (params as { runId: string; segments?: string[] });

  const runId = resolved?.runId ?? "";
  const segments = resolved?.segments ?? [];
  const rawTab = segments[0]?.toLowerCase() as AnalyticsTab;
  const unknownSection = segments.length > 0 && !VALID_TABS.has(rawTab);
  const activeTab: AnalyticsTab = unknownSection || !rawTab ? "overview" : rawTab;
  const ticket = activeTab === "trades" ? segments[1] : undefined;

  const searchParams = useSearchParams();
  const dimension =
    (searchParams?.get("dimension") as PeriodDimension | null) ?? "month";
  const context =
    (searchParams?.get("context") as PeriodContext | null) ?? "all";

  const needsPayload =
    activeTab === "returns" ||
    activeTab === "drawdown" ||
    activeTab === "grouped" ||
    activeTab === "benchmark";
  const { payload, loading, error } = useWorkbenchPayload(runId, needsPayload);

  let panel: ReactNode;
  if (unknownSection) {
    panel = (
      <section aria-label="Unknown analytics section">
        <h2>Unknown analytics section</h2>
        <p>
          This run has no section named &quot;{segments[0]}&quot;. Choose one of
          the sections above to read its evidence.
        </p>
      </section>
    );
  } else if (activeTab === "overview") {
    panel = <OverviewPanel runId={runId} />;
  } else if (activeTab === "trades") {
    panel = ticket ? (
      <TradeDetailPanel runId={runId} ticket={ticket} />
    ) : (
      <TradesPanel runId={runId} />
    );
  } else if (activeTab === "returns") {
    panel = (
      <>
        <ReturnsPanel payload={payload} loading={loading} error={error} />
        <ChartsPanel payload={payload} />
      </>
    );
  } else if (activeTab === "drawdown") {
    panel = (
      <>
        <RiskPanel payload={payload} loading={loading} error={error} />
        <DistributionPanel payload={payload} loading={loading} error={error} />
      </>
    );
  } else if (activeTab === "grouped") {
    panel = (
      <PeriodsPanel
        runId={runId}
        payload={payload}
        dimension={dimension}
        context={context}
      />
    );
  } else if (activeTab === "benchmark") {
    panel = <BenchmarkPanel payload={payload} loading={loading} error={error} />;
  } else {
    panel = (
      <>
        <AnalyticsArtifactDrawer runId={runId} />
        <ProvenancePanel runId={runId} />
        <RealismPanel runId={runId} />
      </>
    );
  }

  return (
    <ProtectedLayout>
      <AnalyticsWorkspace runId={runId} activeTab={activeTab}>
        {panel}
      </AnalyticsWorkspace>
    </ProtectedLayout>
  );
}
