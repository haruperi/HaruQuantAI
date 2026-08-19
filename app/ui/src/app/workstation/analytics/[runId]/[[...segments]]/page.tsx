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
 */

"use client";

import { use, type ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import {
  AnalyticsArtifactDrawer,
  AnalyticsWorkspace,
  OverviewPanel,
  ProvenancePanel,
  RealismPanel,
  TradeDetailPanel,
  TradesPanel,
  type AnalyticsTab,
} from "@/features/analytics-workbench";

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

/** Resolve the panel that owns one Analytics tab. */
function panelFor(
  tab: AnalyticsTab,
  runId: string,
  ticket: string | undefined,
): ReactNode {
  if (tab === "trades") {
    return ticket ? (
      <TradeDetailPanel runId={runId} ticket={ticket} />
    ) : (
      <TradesPanel runId={runId} />
    );
  }
  if (tab === "artifacts") {
    return (
      <>
        <AnalyticsArtifactDrawer runId={runId} />
        <ProvenancePanel runId={runId} />
        <RealismPanel runId={runId} />
      </>
    );
  }
  if (tab === "overview") {
    return <OverviewPanel runId={runId} />;
  }
  return undefined;
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
  const activeTab: AnalyticsTab = VALID_TABS.has(rawTab) ? rawTab : "overview";
  const ticket = activeTab === "trades" ? segments[1] : undefined;

  return (
    <ProtectedLayout>
      <AnalyticsWorkspace runId={runId} activeTab={activeTab}>
        {panelFor(activeTab, runId, ticket)}
      </AnalyticsWorkspace>
    </ProtectedLayout>
  );
}
