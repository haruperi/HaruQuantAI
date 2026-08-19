/**
 * Simulator route (FEAT-UI-31).
 *
 * Hosts the Simulation Workbench in canonical backtest mode, rendering
 * the SimulatorWidget for configuration, progress streaming, and results.
 */

"use client";

import type { ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import { SimulationHome } from "@/features/simulation-workbench";

export default function SimulatorPage(): ReactNode {
  return (
    <ProtectedLayout>
      <SimulationHome initialMode="canonical" />
    </ProtectedLayout>
  );
}
