/**
 * Batch monitor pane (FEAT-UI-31).
 *
 * Shows bounded batch launch progress and updates from ordered stream frames.
 * Snapshot reads are authoritative and used to reconcile stream gaps.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import Link from "next/link";

import {
  ApiClientError,
  apiClients,
  type BatchItem,
  type BatchProjection,
} from "@/clients";
import { consumeStream } from "@/context/streams";
import { simulationWorkbenchRoutes } from "@/clients/routes";
import {
  isBatchActive,
  batchCompletionRatio,
  type StreamState,
} from "./simulation-selectors";
import { useSimulationWorkbenchStore } from "./simulation-store";

/** Resolve a typed error message without inventing a terminal outcome. */
function describeError(cause: unknown): string {
  if (cause instanceof ApiClientError) return cause.message;
  if (cause instanceof Error) return cause.message;
  return "The batch stream is temporarily unavailable.";
}

/** Readable batch error message in an alert banner. */
interface BatchRunMonitorProps {
  batchId: string;
  className?: string;
}

/** Minimal shape of stream payload updates (full projection or item delta). */
type BatchStreamPayload = Record<string, unknown>;

function looksLikeBatchProjection(payload: BatchStreamPayload): payload is BatchProjection {
  return (
    typeof payload.batch_id === "string" &&
    typeof payload.status === "string" &&
    typeof payload.total_items === "number" &&
    typeof payload.completed_items === "number" &&
    typeof payload.failed_items === "number" &&
    typeof payload.cancelled_items === "number"
  );
}

function isKnownBatchItemStatus(value: unknown): value is BatchItem["status"] {
  return (
    value === "queued" ||
    value === "running" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled"
  );
}

function patchBatchFromStream(
  current: BatchProjection | null,
  payload: BatchStreamPayload,
): BatchProjection | null {
  if (looksLikeBatchProjection(payload)) return { ...payload };

  if (!current || typeof payload.item_id !== "string") return current;

  const itemId = payload.item_id;
  const itemStatus =
    isKnownBatchItemStatus(payload.status) ? payload.status : null;
  const runId =
    typeof payload.run_id === "string" ? payload.run_id : null;
  const error =
    payload.error === null || typeof payload.error === "string"
      ? payload.error
      : null;
  const jobId =
    payload.job_id === null || typeof payload.job_id === "string"
      ? payload.job_id
      : undefined;

  if (!itemStatus && runId === null && !jobId && error === null) {
    return current;
  }

  return {
    ...current,
    items: current.items.map((item) =>
      item.item_id === itemId
        ? {
            ...item,
            status: itemStatus ?? item.status,
            run_id: runId ?? item.run_id,
            job_id: jobId ?? item.job_id,
            error: error ?? item.error,
          }
        : item,
    ),
  };
}

/** Canonical batch execution monitor for bounded parameter sweeps. */
export function BatchRunMonitor({
  batchId,
  className = "",
}: BatchRunMonitorProps): ReactNode {
  const setBatchId = useSimulationWorkbenchStore((state) => state.setBatchId);
  const setBatchState = useSimulationWorkbenchStore((state) => state.setBatchState);

  const [batch, setBatch] = useState<BatchProjection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<StreamState>("idle");
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setBatchId(batchId);
    return () => setBatchId(null);
  }, [batchId, setBatchId]);

  const loadBatch = useCallback(async (id: string) => {
    setError(null);
    try {
      const response = await apiClients.simulationWorkbench.getBatch(id);
      if (response.status === "error") {
        throw new Error(response.error.message);
      }
      setBatch(response.data);
    } catch (cause) {
      setError(describeError(cause));
    }
  }, []);

  const refreshBatch = useCallback(
    async (id: string) => {
      const response = await apiClients.simulationWorkbench.getBatch(id);
      if (response.status === "error") {
        throw new Error(response.error.message);
      }
      setBatch(response.data);
      return response.data;
    },
    [],
  );

  const followBatch = useCallback(async (id: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      setState("connecting");
      setBatchState("connecting");
      for await (const event of consumeStream(simulationWorkbenchRoutes.batchStream, {
        pathParams: { batch_id: id },
        signal: controller.signal,
        onGap: async () => {
          await refreshBatch(id);
        },
      })) {
        setState("open");
        setBatchState("open");
        const payload = event.payload as BatchStreamPayload;
        if (!payload || typeof payload !== "object") continue;
        setBatch((current) => patchBatchFromStream(current, payload));
      }

      await refreshBatch(id);
      setState("closed");
      setBatchState("closed");
    } catch (cause) {
      if (controller.signal.aborted) return;
      setState("error");
      setBatchState("error");
      setError(describeError(cause));
    }
  }, [refreshBatch, setBatchState]);

  const cancelBatch = useCallback(async () => {
    if (!batch) return;
    try {
      setError(null);
      const response = await apiClients.simulationWorkbench.cancelBatch(batch.batch_id);
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setBatch(response.data);
    } catch (cause) {
      setError(describeError(cause));
    }
  }, [batch]);

  const retryBatch = useCallback(async () => {
    if (!batch) return;
    try {
      setError(null);
      const response = await apiClients.simulationWorkbench.retryFailedBatch(
        batch.batch_id,
      );
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setBatch(response.data);
    } catch (cause) {
      setError(describeError(cause));
    }
  }, [batch]);

  useEffect(() => {
    void loadBatch(batchId).then(() => {
      void followBatch(batchId);
    });
    return () => abortRef.current?.abort();
  }, [batchId, followBatch, loadBatch]);

  const progress = useMemo(
    () => (batch ? batchCompletionRatio(batch) : 0),
    [batch],
  );
  const active = batch ? isBatchActive(batch.status) : false;

  /**
   * Run identities of successfully completed items.
   *
   * A batch is a set of independent canonical runs. No aggregate portfolio
   * result is inferred from batch membership; a portfolio simulation is an
   * explicitly configured destination.
   */
  const successfulRunIds = useMemo(
    () =>
      (batch?.items ?? [])
        .filter((item) => item.status === "completed" && Boolean(item.run_id))
        .map((item) => item.run_id as string),
    [batch],
  );

  const compareHref = useMemo(
    () =>
      successfulRunIds.length >= 2
        ? `/workstation/analytics/compare?runs=${successfulRunIds
            .map((id) => encodeURIComponent(id))
            .join(",")}`
        : null,
    [successfulRunIds],
  );

  return (
    <section
      className={`simulation-workbench-batch-monitor ${className}`.trim()}
      aria-label="Batch run monitor"
    >
      <header className="flex items-center gap-3 flex-wrap">
        <h3 className="text-lg font-semibold text-white">Batch Run Monitor</h3>
        <span className="text-xs text-slate-400">Stream: {state}</span>
      </header>

      <p className="text-sm text-slate-400 font-mono">
        Batch ID: <span className="text-slate-200">{batchId}</span>
      </p>

      {error && (
        <div className="workflow-simulator__alert mt-3" role="alert">
          {error}
        </div>
      )}

      {batch ? (
        <div className="mt-4">
          <p className="mb-2">
            <strong>Status:</strong> {batch.status}
          </p>
          <p>
            Completed: {batch.completed_items}/{batch.total_items} ({progress}%)
          </p>
          <p>
            Failed: {batch.failed_items} · Cancelled: {batch.cancelled_items} ·
            Concurrency: {batch.concurrency}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void cancelBatch()}
              disabled={!active}
              className="px-3 py-1.5 rounded bg-rose-700 text-white disabled:opacity-50"
            >
              Cancel remaining
            </button>
            <button
              type="button"
              onClick={() => void retryBatch()}
              disabled={!batch || batch.failed_items === 0}
              className="px-3 py-1.5 rounded bg-teal-700 text-white disabled:opacity-50"
            >
              Retry failed
            </button>
            {compareHref ? (
              <Link href={compareHref} className="px-3 py-1.5 rounded bg-slate-700 text-white">
                Compare successful runs
              </Link>
            ) : (
              <span className="px-3 py-1.5 text-slate-500 text-sm">
                Compare successful runs needs at least two completed runs.
              </span>
            )}
          </div>

          <ul className="mt-4 text-sm">
            {batch.items.map((item) => (
              <li key={item.item_id} className="flex items-center gap-2 py-1">
                <span className="font-mono">{item.item_id}</span>
                <span>{item.symbol}</span>
                <span>{item.strategy_id}</span>
                <span className="px-2 py-0.5 rounded bg-slate-800">{item.status}</span>
                <span className="text-slate-400 text-xs">{item.error ?? ""}</span>
                {item.status === "completed" && item.run_id ? (
                  <Link
                    href={`/workstation/analytics/${encodeURIComponent(item.run_id)}/overview`}
                    className="text-teal-300 text-xs underline"
                  >
                    Open Analytics
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="workflow-simulator__empty mt-4">
          Loading batch projection…
        </p>
      )}
    </section>
  );
}
