/**
 * Canonical run monitor (FEAT-UI-31).
 *
 * Loads one run by identity, follows the progress stream, and falls back to
 * authoritative read polling when stream order ends early or cannot continue.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import Link from "next/link";

import { ApiClientError, apiClients, type BacktestRun } from "@/clients";
import { consumeStream } from "@/context/streams";
import { simulatorRoutes } from "@/clients/routes";
import { isRunActive, type StreamState } from "./simulation-selectors";
import { useSimulationWorkbenchStore } from "./simulation-store";
import { SimulationStatusBadge } from "./SimulationStatusBadge";

/** Canonical status-to-progress map (ordered by expected execution order). */
const STAGES: readonly (readonly [string, string])[] = [
  ["market_retrieval", "Market data"],
  ["tick_generation", "Tick generation"],
  ["simulation", "Simulation"],
  ["analytics", "Analytics"],
];

/** Maximum settle polling attempts when stream ends before a terminal payload. */
const SETTLE_ATTEMPTS = 240;
const SETTLE_INTERVAL_MS = 3000;

/** Resolve a typed error message while avoiding invented success claims. */
function describeError(cause: unknown): string {
  if (cause instanceof ApiClientError) return cause.message;
  if (cause instanceof Error) return cause.message;
  return "The simulator endpoint is unavailable.";
}

interface CanonicalRunMonitorProps {
  runId: string;
  className?: string;
}

/** Build a readout for one unknown backend payload. */
function toCanonicalRun(payload: Record<string, unknown>): BacktestRun | null {
  if (typeof payload.status !== "string") return null;
  if (!payload.job_id || typeof payload.job_id !== "string") return null;

  return {
    job_id: payload.job_id,
    status: payload.status as BacktestRun["status"],
    stage: payload.stage === null ? null : String(payload.stage ?? null),
    submitted_at: String(payload.submitted_at ?? ""),
    started_at:
      payload.started_at === null || payload.started_at === undefined
        ? null
        : String(payload.started_at),
    finished_at:
      payload.finished_at === null || payload.finished_at === undefined
        ? null
        : String(payload.finished_at),
    symbol: String(payload.symbol ?? ""),
    timeframe: String(payload.timeframe ?? ""),
    strategy_id: String(payload.strategy_id ?? ""),
    events: Array.isArray(payload.events)
      ? payload.events.map((event) => ({
          sequence:
            typeof event === "object" && event !== null && "sequence" in event
              ? Number((event as { sequence: unknown }).sequence)
              : 0,
          at:
            typeof event === "object" && event !== null && "at" in event
              ? String((event as { at: unknown }).at)
              : "",
          stage:
            typeof event === "object" && event !== null && "stage" in event
              ? String((event as { stage: unknown }).stage)
              : "",
          detail:
            typeof event === "object" && event !== null && "detail" in event
              ? String((event as { detail: unknown }).detail)
              : "",
        }))
      : [],
    result: payload.result === null || payload.result === undefined ? null : payload.result as BacktestRun["result"],
    error: payload.error === null || payload.error === undefined ? null : String(payload.error),
  };
}

/**
 * Monitor one canonical run by identity and display authoritative stream progress.
 */
export function CanonicalRunMonitor({
  runId,
  className = "",
}: CanonicalRunMonitorProps): ReactNode {
  const setCanonicalRunId = useSimulationWorkbenchStore(
    (state) => state.setCanonicalRunId,
  );
  const setCanonicalRunState = useSimulationWorkbenchStore(
    (state) => state.setCanonicalRunState,
  );

  const [run, setRun] = useState<BacktestRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamState, setStreamState] = useState<StreamState>("idle");
  const [cursor, setCursor] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setCanonicalRunId(runId);
    return () => {
      setCanonicalRunId(null);
      abortRef.current?.abort();
    };
  }, [runId, setCanonicalRunId]);

  const settleRun = useCallback(
    async (id: string, signal: AbortSignal): Promise<boolean> => {
      for (let attempt = 0; attempt < SETTLE_ATTEMPTS; attempt += 1) {
        if (signal.aborted) return true;
        const response = await apiClients.simulator.run(id).catch(() => null);
        if (!response || response.status === "error") {
          return false;
        }
        setRun(response.data);
        if (!isRunActive(response.data)) {
          return true;
        }
        await new Promise((resolve) => setTimeout(resolve, SETTLE_INTERVAL_MS));
      }
      return false;
    },
    []
  );

  const followRun = useCallback(async (id: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      setCanonicalRunState("connecting");
      setStreamState("connecting");
      for await (const event of consumeStream(simulatorRoutes.runStream, {
        pathParams: { run_id: id },
        signal: controller.signal,
        onGap: async () => {
          const settled = await settleRun(id, controller.signal);
          if (!settled) throw new Error("stream reconciliation failed");
        },
      })) {
        setCanonicalRunState("open");
        setStreamState("open");
        setCursor(event.sequence);
        const payload = event.payload;
        if (!payload || typeof payload !== "object") continue;

        const canonical = toCanonicalRun(payload as Record<string, unknown>);
        if (canonical) {
          setRun(canonical);
          setCanonicalRunState("closed");
          setStreamState("closed");
          return;
        }

        const stage = String((payload as Record<string, unknown>).stage ?? "");
        const detail = String((payload as Record<string, unknown>).detail ?? "");
        const sequence = Number((payload as Record<string, unknown>).sequence ?? 0);

        setRun((current) =>
          current
            ? {
                ...current,
                status: "running",
                stage,
                events: [...current.events, { sequence, at: new Date().toISOString(), stage, detail }],
              }
            : current,
        );
      }

      const settled = await settleRun(id, controller.signal);
      setCanonicalRunState(settled ? "settled" : "error");
      setStreamState(settled ? "settled" : "error");
      if (!settled) throw new Error("run stream ended without terminal run state");
    } catch (cause) {
      if (controller.signal.aborted) return;
      setCanonicalRunState("error");
      setStreamState("error");
      setError(describeError(cause));
    }
  }, [settleRun, setCanonicalRunState]);

  const loadRun = useCallback(async (id: string) => {
    setError(null);
    setLoading(true);
    try {
      const response = await apiClients.simulator.run(id);
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setRun(response.data);
      if (isRunActive(response.data)) {
        await followRun(id);
      }
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      setLoading(false);
    }
  }, [followRun]);

  const cancelRun = useCallback(async () => {
    if (!run) return;
    abortRef.current?.abort();
    try {
      const response = await apiClients.simulator.cancelRun(run.job_id);
      if (response.status === "success") {
        setRun(response.data);
      } else {
        setError(response.error.message);
      }
    } catch (cause) {
      setError(describeError(cause));
    }
  }, [run]);

  useEffect(() => {
    void loadRun(runId);
    return () => abortRef.current?.abort();
  }, [runId, loadRun]);

  const active = run ? isRunActive(run) : false;
  const runningStages = useMemo(
    () =>
      STAGES.map(([key, title]) => {
        const reached = run?.events.some((item) => item.stage === key) ?? false;
        const current = run?.stage === key && active;
        return (
          <li
            key={key}
            className={
              current
                ? "is-current"
                : reached
                  ? "is-complete"
                  : "is-pending"
            }
          >
            {title}
          </li>
        );
      }),
    [run, active],
  );

  return (
    <section
      className={`simulation-workbench-run-monitor ${className}`.trim()}
      aria-label="Canonical run monitor"
    >
      <header className="flex items-center gap-3 flex-wrap">
        <h3 className="text-lg font-semibold text-white">
          Canonical Run Monitor
        </h3>
        {run ? (
          <SimulationStatusBadge status={run.status} evidenceClass="canonical" />
        ) : (
          <SimulationStatusBadge status="pending" evidenceClass="canonical" />
        )}
      </header>

      <p className="text-sm text-slate-400 font-mono">
        Job ID: <span className="text-slate-200">{runId}</span>
      </p>

      <p className="text-xs text-slate-400" aria-label="Stream connection state">
        Stream: {streamState} · Last-Event-ID:{" "}
        {cursor === null ? "none" : cursor}
      </p>

      {loading && <p>Loading run state...</p>}
      {error && (
        <div className="workflow-simulator__alert" role="alert">
          <strong>Run monitor error:</strong> {error}
        </div>
      )}

      {run && (
        <>
          <div className="mt-2">
            <strong>Symbol:</strong> {run.symbol} ({run.timeframe}){" "}
            <strong>Strategy:</strong> {run.strategy_id}
          </div>

          <div className="mt-4">
            <strong>Status:</strong> {run.status.toUpperCase()}
            {run.stage ? <> · <strong>Stage:</strong> {run.stage}</> : null}
          </div>

          <dl className="mt-2 text-xs text-slate-400">
            <dt>Submitted</dt>
            <dd>{run.submitted_at || "—"}</dd>
            <dt>Started</dt>
            <dd>{run.started_at ?? "—"}</dd>
            <dt>Finished</dt>
            <dd>{run.finished_at ?? "—"}</dd>
          </dl>

          <div className="mt-4">
            <button
              type="button"
              onClick={() => void cancelRun()}
              disabled={!active}
              className="px-3 py-1.5 rounded bg-rose-700 text-white disabled:opacity-50"
            >
              Cancel run
            </button>
          </div>

          {run.error && (
            <p className="mt-3 text-rose-300 text-sm">
              {run.error}
            </p>
          )}

          {run.events.length > 0 && (
            <ul className="workflow-simulator__log mt-4" aria-label="run-log" aria-live="polite">
              {run.events.slice(-12).map((item) => (
                <li key={`${item.sequence}-${item.stage}`}>{item.stage}: {item.detail}</li>
              ))}
            </ul>
          )}

          <ol className="workflow-simulator__stages mt-4">
            {runningStages}
          </ol>

          {run.result && (
            <div className="workflow-simulator__report mt-4">
              <h4>Latest report summary</h4>
              <p className="text-sm">
                {run.result.strategy_label ?? "Strategy"} on {run.result.symbol} {run.result.timeframe}
              </p>
              <p className="text-xs text-slate-400">
                Trades: {run.result.closed_trade_count}
              </p>
              <p className="text-xs text-slate-400 font-mono">
                Canonical run ID: {run.result.run_id}
              </p>
              {run.status === "succeeded" ? (
                <Link
                  href={`/workstation/analytics/${encodeURIComponent(run.result.run_id)}/overview`}
                  className="workflow-simulator__handoff"
                >
                  Open Analytics
                </Link>
              ) : null}
            </div>
          )}
        </>
      )}

      {!run && !loading && !error ? (
        <p className="workflow-simulator__empty">
          No run projection is available for this identifier.
        </p>
      ) : null}
    </section>
  );
}
