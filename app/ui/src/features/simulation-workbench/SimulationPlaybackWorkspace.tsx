/**
 * Immutable trade playback workspace (FEAT-UI-31).
 *
 * Replays one completed run's finalized hash-chained journal around a trade
 * anchor. Playback is read-only in the strongest sense: there is no engine
 * here, no command, and no branch. Frames arrive in journal order over SSE,
 * resume from the last sequence seen, and are rendered exactly as recorded.
 *
 * Order tickets are deliberately never shown. A ticket identifies a live
 * order that an operator could act on; presenting one beside immutable replay
 * evidence would invite exactly the action this surface cannot perform.
 */

"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";

import {
  ApiClientError,
  apiClients,
  journalFrameSchema,
  type JournalFrame,
  type SimulationSession,
} from "@/clients";
import { consumeStream } from "@/context/streams";
import { simulationSessionRoutes } from "@/clients/routes";

/** Maximum frames retained in the browser for one playback session. */
export const MAX_RETAINED_FRAMES = 5_000;

/** Field names that identify a live order and must never be replayed. */
export const SUPPRESSED_FRAME_FIELDS: readonly string[] = [
  "ticket",
  "order_ticket",
  "client_order_id",
  "order_id",
];

/** Resolve a failure message without implying playback completed. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The journal stream is unavailable.";
}

/**
 * Strip every live-order identifier from one recorded frame detail.
 *
 * Args:
 *   detail: Owner-recorded frame detail.
 *
 * Returns:
 *   The same detail without any order-ticket field.
 */
export function withoutOrderTickets(
  detail: Record<string, unknown> | undefined,
): Record<string, unknown> {
  if (!detail) return {};
  return Object.fromEntries(
    Object.entries(detail).filter(
      ([key]) => !SUPPRESSED_FRAME_FIELDS.includes(key),
    ),
  );
}

/** Props accepted by `SimulationPlaybackWorkspace`. */
export interface SimulationPlaybackWorkspaceProps {
  runId: string;
  ticket?: string;
  returnHref?: string;
  className?: string;
}

/** Read-only journal playback around one trade anchor. */
export function SimulationPlaybackWorkspace({
  runId,
  ticket,
  returnHref,
  className = "",
}: SimulationPlaybackWorkspaceProps): ReactNode {
  const [session, setSession] = useState<SimulationSession | null>(null);
  const [frames, setFrames] = useState<JournalFrame[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const follow = useCallback(async (sessionId: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setStreaming(true);
    try {
      for await (const event of consumeStream(simulationSessionRoutes.frames, {
        pathParams: { session_id: sessionId },
        signal: controller.signal,
      })) {
        const parsed = journalFrameSchema.safeParse({
          sequence: event.sequence,
          ...(typeof event.payload === "object" && event.payload !== null
            ? event.payload
            : {}),
        });
        if (!parsed.success) continue;
        setCursor(event.sequence);
        setFrames((current) =>
          current.length >= MAX_RETAINED_FRAMES
            ? current
            : [...current, parsed.data],
        );
      }
    } catch (cause) {
      if (!controller.signal.aborted) setError(failureMessage(cause));
    } finally {
      setStreaming(false);
    }
  }, []);

  const open = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClients.simulationSessions.createSession({
        run_id: runId,
        ...(ticket ? { anchor_ticket: ticket } : {}),
      });
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setSession(response.data);
      await follow(response.data.session_id);
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [runId, ticket, follow]);

  useEffect(() => {
    void open();
    return () => abortRef.current?.abort();
  }, [open]);

  const visibleFrames = useMemo(
    () =>
      frames.map((frame) => ({
        sequence: frame.sequence,
        at: frame.at ?? "",
        eventType: frame.event_type ?? "",
        frameHash: frame.frame_hash ?? "",
        previousHash: frame.previous_hash ?? "",
        detail: withoutOrderTickets(frame.detail),
      })),
    [frames],
  );

  return (
    <section
      className={`simulation-playback ${className}`.trim()}
      aria-label="Immutable trade playback"
    >
      <header className="simulation-playback__header">
        <h3>Trade playback</h3>
        <p className="simulation-playback__note">
          This is a read-only replay of a finalized journal. No order can be
          placed, modified, or cancelled here.
        </p>
        {returnHref ? (
          <Link href={returnHref} className="simulation-playback__return">
            Return to Analytics
          </Link>
        ) : null}
      </header>

      <dl className="simulation-playback__facts">
        <dt>Run</dt>
        <dd className="font-mono">{runId}</dd>
        <dt>Trade anchor</dt>
        <dd className="font-mono">{ticket ?? "whole run"}</dd>
        <dt>Playback session</dt>
        <dd className="font-mono">{session?.session_id ?? "—"}</dd>
        <dt>Journal reference</dt>
        <dd className="font-mono">{session?.journal_ref ?? "—"}</dd>
        <dt>Journal hash</dt>
        <dd className="font-mono">{session?.journal_hash ?? "—"}</dd>
        <dt>Result hash</dt>
        <dd className="font-mono">{session?.result_hash ?? "—"}</dd>
        <dt>Engine version</dt>
        <dd>{session?.engine_version ?? "—"}</dd>
        <dt>Last-Event-ID</dt>
        <dd>{cursor === null ? "none" : cursor}</dd>
        <dt>Stream</dt>
        <dd>{streaming ? "open" : "closed"}</dd>
      </dl>

      {loading ? <p role="status">Opening playback session…</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      <table className="simulation-playback__frames">
        <caption className="sr-only">Ordered journal frames</caption>
        <thead>
          <tr>
            <th scope="col">Sequence</th>
            <th scope="col">At</th>
            <th scope="col">Event</th>
            <th scope="col">Frame hash</th>
            <th scope="col">Previous hash</th>
            <th scope="col">Detail</th>
          </tr>
        </thead>
        <tbody>
          {visibleFrames.map((frame) => (
            <tr key={frame.sequence}>
              <td>{frame.sequence}</td>
              <td>{frame.at || "—"}</td>
              <td>{frame.eventType || "—"}</td>
              <td className="font-mono">{frame.frameHash || "—"}</td>
              <td className="font-mono">{frame.previousHash || "—"}</td>
              <td>{JSON.stringify(frame.detail)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {visibleFrames.length === 0 && !loading && !error ? (
        <p>No journal frame has been replayed yet.</p>
      ) : null}
    </section>
  );
}
