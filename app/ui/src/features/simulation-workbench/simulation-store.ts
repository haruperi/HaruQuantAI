/**
 * Simulation workbench display store (FEAT-UI-31).
 *
 * Holds only UI-owned navigation/context state. Run projection payloads stay in
 * component-local state to avoid stale data sharing across independent monitors.
 */

"use client";

import { create } from "zustand";

import type { StreamState } from "./simulation-selectors";
import type { SimulationMode } from "./SimulationWorkbench";

/** Minimal display state shared across workbench panes. */
export interface SimulationWorkbenchStore {
  activeMode: SimulationMode;
  canonicalRunId: string | null;
  batchId: string | null;
  canonicalRunState: StreamState;
  batchState: StreamState;
  setActiveMode: (mode: SimulationMode) => void;
  setCanonicalRunId: (runId: string | null) => void;
  setBatchId: (batchId: string | null) => void;
  setCanonicalRunState: (state: StreamState) => void;
  setBatchState: (state: StreamState) => void;
  clear: () => void;
}

export const useSimulationWorkbenchStore = create<SimulationWorkbenchStore>((set) => ({
  activeMode: "canonical",
  canonicalRunId: null,
  batchId: null,
  canonicalRunState: "idle",
  batchState: "idle",
  setActiveMode: (mode) => set({ activeMode: mode }),
  setCanonicalRunId: (runId) => set({ canonicalRunId: runId }),
  setBatchId: (batchId) => set({ batchId }),
  setCanonicalRunState: (state) => set({ canonicalRunState: state }),
  setBatchState: (state) => set({ batchState: state }),
  clear: () =>
    set({
      activeMode: "canonical",
      canonicalRunId: null,
      batchId: null,
      canonicalRunState: "idle",
      batchState: "idle",
    }),
}));
