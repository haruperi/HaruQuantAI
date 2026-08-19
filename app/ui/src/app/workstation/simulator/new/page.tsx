/**
 * New simulation run route (FEAT-UI-31).
 *
 * Dedicated route for configuring and submitting a new canonical backtest run.
 */

"use client";

import type { ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import { SimulationHome } from "@/features/simulation-workbench";

export default function NewSimulationPage(): ReactNode {
  return (
    <ProtectedLayout>
      <SimulationHome initialMode="canonical" />
    </ProtectedLayout>
  );
}
