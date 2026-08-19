/**
 * Analytics workbench display store (FEAT-UI-32).
 *
 * Holds only the operator's selection and presentation choices. No metric,
 * comparison result, or report payload is cached here: evidence is read from
 * the owner each time so a stale figure can never outlive the run it
 * described.
 */

"use client";

import { create } from "zustand";

import type { ComparisonMetric } from "@/clients";
import { toggleSelection } from "./analytics-selectors";

/** Selection and presentation state shared across Analytics surfaces. */
export interface AnalyticsWorkbenchStore {
  selectedRunIds: string[];
  metric: ComparisonMetric;
  setMetric: (metric: ComparisonMetric) => void;
  toggleRun: (runId: string) => void;
  setSelection: (runIds: readonly string[]) => void;
  clearSelection: () => void;
}

export const useAnalyticsWorkbenchStore = create<AnalyticsWorkbenchStore>(
  (set) => ({
    selectedRunIds: [],
    metric: "summary",
    setMetric: (metric) => set({ metric }),
    toggleRun: (runId) =>
      set((state) => ({
        selectedRunIds: toggleSelection(state.selectedRunIds, runId),
      })),
    setSelection: (runIds) => set({ selectedRunIds: [...runIds] }),
    clearSelection: () => set({ selectedRunIds: [] }),
  }),
);
