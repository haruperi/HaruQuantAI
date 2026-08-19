/**
 * Display-only Research workbench store (FEAT-UI-28).
 *
 * The URL is the primary navigation state — experiment, run, and stage all
 * live in the route. This store holds only what the URL cannot: an unsaved
 * builder draft, view filters, collapsed sections, the comparison selection,
 * and stream-connection metadata.
 *
 * It deliberately holds no dataset rows, no report, no scorecard, and no
 * Research decision. Those are server-owned and are refetched by identity.
 */

"use client";

import { create } from "zustand";

/** Unsaved run-builder draft. Cleared once a run is queued. */
export interface RunBuilderDraft {
  experimentId: string | null;
  experimentName: string;
  hypothesis: string;
  notes: string;
  tags: string;
  symbol: string;
  timeframe: string;
  sourceId: string;
  start: string;
  end: string;
  barLimit: number;
  assetClass: string;
  preset: string;
  selectedStages: string[];
  reason: string;
  forceRerun: boolean;
  saveArtifacts: boolean;
  seed: string;
  bootstrapSamples: string;
  permutationSamples: string;
  nullSamples: string;
  correction: string;
  featureWindows: string;
  forwardHorizons: string;
  enableMarketStructureQuality: boolean | null;
  modelingClusters: string;
  modelingPcaComponents: string;
  continueOnStudyError: boolean | null;
  sessionTimezone: string;
}

/** Live connection state of one run's ordered progress stream. */
export type StreamConnectionState =
  | "idle"
  | "connecting"
  | "open"
  | "closed"
  | "error";

/** Display-only workbench state. */
export interface ResearchStoreState {
  draft: RunBuilderDraft;
  comparisonSelection: string[];
  collapsedSections: Record<string, boolean>;
  filters: Record<string, string>;
  streamState: StreamConnectionState;
  streamRunId: string | null;
  streamCursor: number;
  setDraft: (patch: Partial<RunBuilderDraft>) => void;
  resetDraft: () => void;
  toggleComparisonRun: (runId: string) => void;
  clearComparison: () => void;
  toggleSection: (key: string) => void;
  setFilter: (key: string, value: string) => void;
  setStream: (
    state: StreamConnectionState,
    runId: string | null,
    cursor?: number
  ) => void;
}

/** The empty draft a fresh builder starts from. */
export const EMPTY_DRAFT: RunBuilderDraft = {
  experimentId: null,
  experimentName: "",
  hypothesis: "",
  notes: "",
  tags: "",
  symbol: "",
  timeframe: "H1",
  sourceId: "",
  start: "",
  end: "",
  barLimit: 5000,
  assetClass: "",
  preset: "standard_edge",
  selectedStages: [],
  reason: "",
  forceRerun: false,
  saveArtifacts: true,
  seed: "",
  bootstrapSamples: "",
  permutationSamples: "",
  nullSamples: "",
  correction: "",
  featureWindows: "",
  forwardHorizons: "",
  enableMarketStructureQuality: null,
  modelingClusters: "",
  modelingPcaComponents: "",
  continueOnStudyError: null,
  sessionTimezone: "",
};

/** Maximum runs the server accepts in one comparison. */
export const MAX_COMPARISON_RUNS = 5;

/** Display-only Research workbench store. */
export const useResearchStore = create<ResearchStoreState>((set) => ({
  draft: { ...EMPTY_DRAFT },
  comparisonSelection: [],
  collapsedSections: {},
  filters: {},
  streamState: "idle",
  streamRunId: null,
  streamCursor: 0,
  setDraft: (patch) =>
    set((state) => ({ draft: { ...state.draft, ...patch } })),
  resetDraft: () => set({ draft: { ...EMPTY_DRAFT } }),
  toggleComparisonRun: (runId) =>
    set((state) => {
      if (state.comparisonSelection.includes(runId)) {
        return {
          comparisonSelection: state.comparisonSelection.filter(
            (id) => id !== runId
          ),
        };
      }
      if (state.comparisonSelection.length >= MAX_COMPARISON_RUNS) {
        return state;
      }
      return { comparisonSelection: [...state.comparisonSelection, runId] };
    }),
  clearComparison: () => set({ comparisonSelection: [] }),
  toggleSection: (key) =>
    set((state) => ({
      collapsedSections: {
        ...state.collapsedSections,
        [key]: !state.collapsedSections[key],
      },
    })),
  setFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),
  setStream: (streamState, streamRunId, streamCursor) =>
    set((state) => ({
      streamState,
      streamRunId,
      streamCursor: streamCursor ?? state.streamCursor,
    })),
}));
