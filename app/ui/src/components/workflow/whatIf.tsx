/**
 * Live what-if exploration over a resumable Simulation session (CAP-UI-013).
 *
 * This is the counterpart to `PlaybackView`, and the distinction matters more
 * than the shared vocabulary suggests. Playback replays a *finalized* journal
 * and can never change an outcome. A live session drives an engine that has
 * not finished: it advances on demand and can be branched at the current
 * cursor to explore an alternative without disturbing the parent.
 *
 * Three properties the view is responsible for surfacing honestly:
 *
 * - **Results are advisory.** A live session is not a recorded, reproducible
 *   run. The view labels it as such rather than letting a partial exploration
 *   read like a completed backtest.
 * - **Stepping is cumulative, not repeatable.** The backend deliberately does
 *   not accept an idempotency key on step, so a retry advances further rather
 *   than replaying. The cursor returned by the server is authoritative; the
 *   view never predicts it locally.
 * - **Branch lineage is explicit.** A branch names its parent and its
 *   divergence point, so an alternative can never be mistaken for the baseline.
 */

"use client";

import { useCallback, useState, type ReactNode } from "react";

import { ApiClientError, apiClients, type LiveSession } from "@/clients";

/** Props accepted by `WhatIfView`. */
export interface WhatIfViewProps {
  className?: string;
  /** Ticks advanced per step. Bounded by the backend at 10,000. */
  stepSize?: number;
}

const DEFAULT_STEP_SIZE = 100;

/** One session shown in the lineage list. */
interface SessionRow {
  readonly sessionId: string;
  readonly parent: string | null;
  readonly cursor: number;
  readonly divergence: number | null;
}

/** Read a session row out of the opaque Simulator-owned payload. */
function toRow(payload: LiveSession | null): SessionRow | null {
  if (!payload) {
    return null;
  }
  const sessionId = String(payload.session_id ?? "");
  if (!sessionId) {
    return null;
  }
  const parent = payload.parent_session_id;
  const divergence = payload.divergence_index;
  return {
    sessionId,
    parent: typeof parent === "string" ? parent : null,
    cursor: Number(payload.cursor ?? 0),
    divergence: typeof divergence === "number" ? divergence : null,
  };
}

/** Live what-if session view. */
export function WhatIfView({
  className,
  stepSize = DEFAULT_STEP_SIZE,
}: WhatIfViewProps = {}): ReactNode {
  const [requestJson, setRequestJson] = useState("");
  const [overridesJson, setOverridesJson] = useState("{}");
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const record = useCallback((payload: LiveSession | null) => {
    const row = toRow(payload);
    if (!row) {
      setError("The gateway returned no live session identifier.");
      return;
    }
    setSessions((current) => [
      ...current.filter((item) => item.sessionId !== row.sessionId),
      row,
    ]);
    setActiveId(row.sessionId);
  }, []);

  const report = useCallback((caught: unknown) => {
    if (caught instanceof ApiClientError) {
      setError(caught.message);
    } else if (caught instanceof SyntaxError) {
      setError("The request or overrides field is not valid JSON.");
    } else {
      setError("The live session operation failed for an unexpected reason.");
    }
  }, []);

  const open = useCallback(async () => {
    setError(null);
    setBusy(true);
    try {
      const body = JSON.parse(requestJson || "{}") as Record<string, unknown>;
      const created = await apiClients.liveSimulation.createSession(body);
      record(created.data);
    } catch (caught) {
      report(caught);
    } finally {
      setBusy(false);
    }
  }, [requestJson, record, report]);

  const step = useCallback(async () => {
    if (!activeId) {
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const advanced = await apiClients.liveSimulation.step(activeId, stepSize);
      record(advanced.data);
    } catch (caught) {
      report(caught);
    } finally {
      setBusy(false);
    }
  }, [activeId, stepSize, record, report]);

  const branch = useCallback(async () => {
    if (!activeId) {
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const overrides = JSON.parse(overridesJson || "{}") as Record<
        string,
        unknown
      >;
      const branched = await apiClients.liveSimulation.branch(
        activeId,
        overrides
      );
      record(branched.data);
    } catch (caught) {
      report(caught);
    } finally {
      setBusy(false);
    }
  }, [activeId, overridesJson, record, report]);

  const close = useCallback(async () => {
    if (!activeId) {
      return;
    }
    setError(null);
    setBusy(true);
    const closing = activeId;
    try {
      await apiClients.liveSimulation.closeSession(closing);
      setSessions((current) =>
        current.filter((item) => item.sessionId !== closing)
      );
      setActiveId(null);
    } catch (caught) {
      report(caught);
    } finally {
      setBusy(false);
    }
  }, [activeId, report]);

  const active = sessions.find((item) => item.sessionId === activeId) ?? null;

  return (
    <section className={className} aria-labelledby="what-if-heading">
      <h2 id="what-if-heading">Live what-if</h2>
      <p>
        Drives a resumable simulation engine. Results are advisory: a live
        session is an exploration, not a recorded, reproducible run.
      </p>

      <div>
        <label htmlFor="what-if-request">Simulation request (JSON)</label>
        <textarea
          id="what-if-request"
          value={requestJson}
          onChange={(event) => setRequestJson(event.target.value)}
          disabled={busy}
        />
        <button type="button" onClick={() => void open()} disabled={busy}>
          Open session
        </button>
      </div>

      <div>
        <label htmlFor="what-if-overrides">Branch overrides (JSON)</label>
        <textarea
          id="what-if-overrides"
          value={overridesJson}
          onChange={(event) => setOverridesJson(event.target.value)}
          disabled={busy}
        />
        <button
          type="button"
          onClick={() => void branch()}
          disabled={busy || !activeId}
        >
          Branch here
        </button>
      </div>

      <div>
        <button
          type="button"
          onClick={() => void step()}
          disabled={busy || !activeId}
        >
          Step {stepSize}
        </button>
        <button
          type="button"
          onClick={() => void close()}
          disabled={busy || !activeId}
        >
          Close session
        </button>
      </div>

      <p aria-live="polite">
        {active
          ? `Active ${active.sessionId} — cursor ${active.cursor}`
          : "No active session."}
      </p>

      {error ? <p role="alert">{error}</p> : null}

      <ol aria-label="Session lineage">
        {sessions.map((item) => (
          <li key={item.sessionId}>
            <button type="button" onClick={() => setActiveId(item.sessionId)}>
              {item.sessionId}
            </button>
            <span>cursor {item.cursor}</span>
            {item.parent ? (
              <span>
                branched from {item.parent} at {item.divergence ?? "?"}
              </span>
            ) : (
              <span>baseline</span>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
