/**
 * Simulator route (cross-domain coverage for the Research workbench).
 *
 * Monte Carlo and canonical backtests are owned by Simulation, not Research.
 * This route hosts the already-owned `SimulatorWidget` so a researcher can
 * continue from a Research run without Research owning execution.
 */

"use client";

import type { ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import { SimulatorWidget } from "@/features/simulator";

export default function Page(): ReactNode {
  return (
    <ProtectedLayout>
      <main className="research-root">
        <header className="research-page__head">
          <p className="research-eyebrow">Simulation</p>
          <h1>Simulator</h1>
          <p>
            Canonical backtest execution. Research links here and hands over
            identifiers only; it never runs a backtest itself.
          </p>
        </header>
        <SimulatorWidget />
      </main>
    </ProtectedLayout>
  );
}
