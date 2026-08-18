/**
 * Analytics landing page (FEAT-UI-32).
 *
 * Hosts the Analytics Workspace overview and run catalogue handoff.
 */

"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { Play } from "lucide-react";

import { ProtectedLayout } from "@/app/protected-layout";
import { AnalyticsWorkspace } from "@/features/analytics-workbench";

export default function AnalyticsLandingPage(): ReactNode {
  return (
    <ProtectedLayout>
      <AnalyticsWorkspace>
        <div className="flex flex-col items-center justify-center p-12 text-center gap-4">
          <p className="text-slate-400 max-w-md">
            Select a simulation run from the catalogue or launch a new canonical backtest to inspect full trade ledgers, drawdown curves, and performance scorecards.
          </p>
          <Link
            href="/workstation/simulator/new"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded bg-teal-600 hover:bg-teal-500 text-white shadow"
          >
            <Play className="w-4 h-4" aria-hidden="true" />
            <span>Launch Simulation</span>
          </Link>
        </div>
      </AnalyticsWorkspace>
    </ProtectedLayout>
  );
}
