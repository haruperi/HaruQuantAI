/**
 * Completed-run Simulation journal playback (CAP-UI-012, frontend tier).
 *
 * This view replays the finalized hash-chained journal of a run that has
 * already completed. It is deliberately not a live simulator: there is no
 * step, no branch, and no parameter control. A stateful live engine does now
 * exist — see `WhatIfView` — but it is a separate surface on purpose, because
 * a finalized run is evidence and evidence must not be steerable. Nothing
 * here can alter a recorded outcome.
 *
 * Frames arrive over SSE through `consumeStream`, which validates monotonic
 * sequence, filters heartbeats, surfaces terminal errors, and reports gaps.
 * On a gap the view stops and says so rather than presenting a partial journal
 * as if it were complete — a silently truncated replay would be indistinguishable
 * from a shorter run.
 */

"use client";

import { useCallback, useRef, useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import { consumeStream, StreamGapError } from "@/context";

/** Props accepted by `PlaybackView`. */
export interface PlaybackViewProps {
  className?: string;
  /** Maximum frames retained in view. Bounds memory on a long journal. */
  maxFrames?: number;
}

const DEFAULT_MAX_FRAMES = 500;

/** One rendered journal frame. */
interface Frame {
  readonly sequence: number;
  readonly type: string;
  readonly summary: string;
}

/** Completed-run journal playback view. */
export function PlaybackView({
  className,
  maxFrames = DEFAULT_MAX_FRAMES,
}: PlaybackViewProps = {}): ReactNode {
  const [runId, setRunId] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [frames, setFrames] = useState<Frame[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "streaming" | "done">(
    "idle"
  );
  const [error, setError] = useState<string | null>(null);
  const [truncated, setTruncated] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus((current) => (current === "streaming" ? "done" : current));
  }, []);

  const start = useCallback(async () => {
    if (!runId.trim()) {
      setError("A completed run identifier is required.");
      return;
    }
    stop();
    setFrames([]);
    setTruncated(false);
    setError(null);
    setStatus("loading");

    try {
      const created = await apiClients.simulationSessions.createSession({
        run_id: runId.trim(),
      });
      const session = created.data as Record<string, unknown> | null;
      const id = session ? String(session.session_id ?? "") : "";
      if (!id) {
        setError("The gateway returned no playback session identifier.");
        setStatus("idle");
        return;
      }
      setSessionId(id);
      setStatus("streaming");

      const controller = new AbortController();
      abortRef.current = controller;

      for await (const event of consumeStream(
        apiClients.simulationSessions.framesContract,
        { pathParams: { session_id: id }, signal: controller.signal }
      )) {
        const payload = (event.payload ?? {}) as Record<string, unknown>;
        setFrames((current) => {
          if (current.length >= maxFrames) {
            setTruncated(true);
            return current;
          }
          return [
            ...current,
            {
              sequence: event.sequence,
              type: String(payload.event_type ?? event.event_type),
              summary: JSON.stringify(payload),
            },
          ];
        });
      }
      setStatus("done");
    } catch (caught) {
      if (caught instanceof StreamGapError) {
        setError(
          "The journal stream reported a gap. Playback stopped; restart to " +
            "replay the run from the beginning."
        );
      } else if (caught instanceof ApiClientError) {
        setError(caught.message);
      } else {
        setError("Playback failed for an unexpected reason.");
      }
      setStatus("done");
    } finally {
      abortRef.current = null;
    }
  }, [runId, maxFrames, stop]);

  return (
    <section className={className} aria-labelledby="playback-heading">
      <h2 id="playback-heading">Journal playback</h2>
      <p>
        Replays the finalized journal of a completed run. Playback is read-only:
        it cannot change a recorded result.
      </p>

      <div>
        <label htmlFor="playback-run-id">Completed run ID</label>
        <input
          id="playback-run-id"
          value={runId}
          onChange={(event) => setRunId(event.target.value)}
          disabled={status === "streaming" || status === "loading"}
        />
        <button
          type="button"
          onClick={() => void start()}
          disabled={status === "streaming" || status === "loading"}
        >
          {status === "loading" ? "Opening session…" : "Play"}
        </button>
        <button
          type="button"
          onClick={stop}
          disabled={status !== "streaming"}
        >
          Stop
        </button>
      </div>

      {sessionId ? <p>Session: {sessionId}</p> : null}

      <p aria-live="polite">
        {status === "streaming"
          ? `Streaming — ${frames.length} frame(s)`
          : status === "done"
            ? `Finished — ${frames.length} frame(s)`
            : null}
      </p>

      {truncated ? (
        <p role="status">
          Showing the first {maxFrames} frames. The journal continues beyond
          this view.
        </p>
      ) : null}

      {error ? <p role="alert">{error}</p> : null}

      <ol>
        {frames.map((frame) => (
          <li key={frame.sequence}>
            <span>#{frame.sequence}</span> <span>{frame.type}</span>
            <code>{frame.summary}</code>
          </li>
        ))}
      </ol>
    </section>
  );
}
