/**
 * Data-loading hooks for the Research workbench (FEAT-UI-28).
 *
 * Every hook fetches server-owned evidence by identity and keeps nothing
 * authoritative in the browser. A run that is still in flight is followed by
 * its ordered SSE progress stream, with a bounded poll as the fallback when
 * the stream is unavailable — the same pattern the canonical Simulator uses.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, apiClients, isApiSuccessResponse } from "@/clients";
import type {
  ApiResponse,
  ResearchArtifactList,
  ResearchAutomationBatch,
  ResearchComparison,
  ResearchDashboard,
  ResearchDrift,
  ResearchExpectancy,
  ResearchExperimentDetail,
  ResearchExperimentSummary,
  ResearchPresetCatalogue,
  ResearchRunDetail,
  ResearchRunReport,
  ResearchRunSummary,
  ResearchStageView,
} from "@/clients";

import { useResearchStore } from "./research-store";
import { isRunActive } from "./research-selectors";

/** Poll interval used while a run is queued or running. */
const POLL_INTERVAL_MS = 2500;

/** One asynchronous evidence load. */
export interface AsyncEvidence<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/** Translate any thrown transport failure into a displayable message. */
function messageOf(cause: unknown): string {
  if (cause instanceof ApiClientError) return `${cause.code}: ${cause.message}`;
  if (cause instanceof Error) return cause.message;
  return "unavailable";
}

/**
 * Run one client call and expose its result, loading, and failure state.
 *
 * `deps` identifies the resource. Passing `null` as the loader disables the
 * fetch entirely, which is how pages express "nothing selected yet".
 */
function useEvidence<T>(
  loader: (() => Promise<ApiResponse<T>>) | null,
  deps: readonly unknown[]
): AsyncEvidence<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(loader !== null);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  useEffect(() => {
    const current = loaderRef.current;
    if (current === null) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    void (async () => {
      try {
        const response = await current();
        if (cancelled) return;
        if (isApiSuccessResponse(response)) {
          setData(response.data);
          setError(null);
        } else {
          setError(response.error.message);
          setData(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(messageOf(cause));
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { data, loading, error, reload };
}

/** Load the server-owned preset catalogue. */
export function usePresets(): AsyncEvidence<ResearchPresetCatalogue> {
  return useEvidence<ResearchPresetCatalogue>(
    () => apiClients.research.listPresets(),
    []
  );
}

/** Load the research ledger for the entry page. */
export function useDashboard(): AsyncEvidence<ResearchDashboard> {
  return useEvidence<ResearchDashboard>(
    () => apiClients.research.getDashboard(),
    []
  );
}

/** Load every owned experiment. */
export function useExperiments(): AsyncEvidence<{
  experiments: ResearchExperimentSummary[];
}> {
  return useEvidence<{ experiments: ResearchExperimentSummary[] }>(
    () => apiClients.research.listExperiments(),
    []
  );
}

/** Load one experiment with its run ledger. */
export function useExperiment(
  experimentId: string | null
): AsyncEvidence<ResearchExperimentDetail> {
  return useEvidence<ResearchExperimentDetail>(
    experimentId ? () => apiClients.research.getExperiment(experimentId) : null,
    [experimentId]
  );
}

/** Load owned runs, optionally filtered by experiment or batch. */
export function useRuns(filters?: {
  experimentId?: string;
  batchId?: string;
}): AsyncEvidence<{ runs: ResearchRunSummary[] }> {
  return useEvidence<{ runs: ResearchRunSummary[] }>(
    () => apiClients.research.listRuns(filters),
    [filters?.experimentId, filters?.batchId]
  );
}

/**
 * Load one run and follow it while it is in flight.
 *
 * The ordered SSE stream drives refreshes when it is available; a bounded
 * interval poll covers the case where the stream cannot be opened, so a run
 * still settles rather than appearing stuck.
 */
export function useRun(runId: string | null): AsyncEvidence<ResearchRunDetail> {
  const evidence = useEvidence<ResearchRunDetail>(
    runId ? () => apiClients.research.getRun(runId) : null,
    [runId]
  );
  const setStream = useResearchStore((state) => state.setStream);
  const status = evidence.data?.status ?? null;
  const active = isRunActive(status);
  const reload = evidence.reload;

  useEffect(() => {
    if (!runId || !active) {
      setStream("idle", null);
      return;
    }
    const controller = new AbortController();
    let closed = false;
    setStream("connecting", runId, 0);

    void (async () => {
      try {
        for await (const event of apiClients.research.openRunEvents(runId, {
          signal: controller.signal,
        })) {
          if (closed) return;
          setStream("open", runId, event.sequence);
          reload();
          if (event.event_type === "payload") {
            const stage = (event.payload as Record<string, unknown> | undefined)?.[
              "stage"
            ];
            if (
              stage === "completed" ||
              stage === "failed" ||
              stage === "cancelled"
            ) {
              setStream("closed", runId, event.sequence);
              return;
            }
          }
        }
        if (!closed) setStream("closed", runId);
      } catch {
        if (!closed) setStream("error", runId);
      }
    })();

    const timer = setInterval(reload, POLL_INTERVAL_MS);
    return () => {
      closed = true;
      controller.abort();
      clearInterval(timer);
    };
  }, [runId, active, reload, setStream]);

  return evidence;
}

/** Load one navigable stage view. */
export function useStage(
  runId: string | null,
  stage: string | null,
  query?: { scenarioId?: string; profileId?: string }
): AsyncEvidence<ResearchStageView> {
  return useEvidence<ResearchStageView>(
    runId && stage
      ? () => apiClients.research.getStage(runId, stage, query)
      : null,
    [runId, stage, query?.scenarioId, query?.profileId]
  );
}

/** Load the registered report for the diagnostic viewer. */
export function useRunReport(
  runId: string | null
): AsyncEvidence<ResearchRunReport> {
  return useEvidence<ResearchRunReport>(
    runId ? () => apiClients.research.getRunReport(runId) : null,
    [runId]
  );
}

/** Load the artifact references retained for one run. */
export function useArtifacts(
  runId: string | null
): AsyncEvidence<ResearchArtifactList> {
  return useEvidence<ResearchArtifactList>(
    runId ? () => apiClients.research.listArtifacts(runId) : null,
    [runId]
  );
}

/** Load one automation batch and follow it while symbols are pending. */
export function useAutomationBatch(
  batchId: string | null
): AsyncEvidence<ResearchAutomationBatch> {
  const evidence = useEvidence<ResearchAutomationBatch>(
    batchId ? () => apiClients.research.getAutomationBatch(batchId) : null,
    [batchId]
  );
  const pending = evidence.data?.counts.pending ?? 0;
  const reload = evidence.reload;
  useEffect(() => {
    if (!batchId || pending <= 0) return;
    const timer = setInterval(reload, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [batchId, pending, reload]);
  return evidence;
}

/** Load the approved expectancy profile. */
export function useExpectancy(query?: {
  profileId?: string;
  strategyRef?: string;
}): AsyncEvidence<ResearchExpectancy> {
  return useEvidence<ResearchExpectancy>(
    () => apiClients.research.getExpectancy(query),
    [query?.profileId, query?.strategyRef]
  );
}

/** Load the latest performance-drift evidence. */
export function useDrift(query?: {
  profileId?: string;
}): AsyncEvidence<ResearchDrift> {
  return useEvidence<ResearchDrift>(
    () => apiClients.research.getDrift(query),
    [query?.profileId]
  );
}

/** Request one server-derived comparison across selected runs. */
export function useComparison(runIds: readonly string[]): AsyncEvidence<ResearchComparison> {
  return useEvidence<ResearchComparison>(
    runIds.length >= 2 ? () => apiClients.research.compareRuns([...runIds]) : null,
    [runIds.join(",")]
  );
}
