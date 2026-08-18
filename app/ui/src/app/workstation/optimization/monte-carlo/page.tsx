/**
 * Monte Carlo route (cross-domain coverage for the Research workbench).
 *
 * V1 placed a Monte Carlo Lab under Edge Lab. In V2 the capability belongs to
 * Simulation and Optimization, so this route hosts the owned Optimization
 * surface and links to the Simulator rather than duplicating either.
 */

"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";
import { OptimizationView } from "@/components/workflow";

export default function Page(): ReactNode {
  return (
    <ProtectedLayout>
      <main className="research-root">
        <header className="research-page__head">
          <p className="research-eyebrow">Optimization</p>
          <h1>Monte Carlo and robustness</h1>
          <p>
            Owned by Optimization and Simulation. Research supplies the
            hypothesis and artifact references; the execution and its advisory
            evidence belong here.
          </p>
          <div className="research-links">
            <Link className="research-button" href="/workstation/simulator">
              Open Simulator
            </Link>
            <Link className="research-button" href="/workstation/research">
              Back to Research
            </Link>
          </div>
        </header>
        <OptimizationView />
      </main>
    </ProtectedLayout>
  );
}
