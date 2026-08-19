/**
 * Run-level warning surface (FEAT-UI-28).
 *
 * Warnings are grouped by the severity Research assigned. Nothing is filtered
 * out: a research ledger that hides its caveats is not evidence.
 */

"use client";

import type { ReactNode } from "react";

import type { ResearchWarning } from "@/clients";

import { Section, WarningList } from "./evidence";

/** Props accepted by `ResearchWarnings`. */
export interface ResearchWarningsProps {
  warnings: readonly ResearchWarning[];
  title?: string;
}

/** Grouped warning panel. */
export function ResearchWarnings({
  warnings,
  title = "Warnings",
}: ResearchWarningsProps): ReactNode {
  return (
    <Section
      title={`${title} (${warnings.length})`}
      description="Grouped by the severity Research assigned. None are suppressed."
    >
      <WarningList warnings={warnings} />
    </Section>
  );
}
