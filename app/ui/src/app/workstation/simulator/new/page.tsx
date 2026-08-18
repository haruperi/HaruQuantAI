/**
 * New simulation run route (FEAT-UI-31).
 *
 * Dedicated route for configuring and submitting a new canonical backtest run.
 */

"use client";

import type { ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import { SimulationWorkbench } from "@/features/simulation-workbench";
import { SimulatorWidget } from "@/features/simulator";

export default function NewSimulationPage(): ReactNode {
  return (
    <ProtectedLayout>
      <SimulationWorkbench initialMode="canonical">
        <SimulatorWidget />
      </SimulationWorkbench>
    </ProtectedLayout>
  );
}
