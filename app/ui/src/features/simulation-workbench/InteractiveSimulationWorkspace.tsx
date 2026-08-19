/**
 * Interactive simulation workspace (FEAT-UI-31).
 *
 * Owns the browser-side pacing scheduler for one live session. The scheduler
 * only ever asks the server to advance: the cursor this workspace shows is
 * always the cursor the server last reported. Four rules keep that true:
 *
 * - Pause stops the scheduler outright rather than muting its display.
 * - Losing page visibility pauses, so a backgrounded tab cannot silently
 *   advance a session nobody is watching.
 * - Reconnecting reads authoritative state before resuming.
 * - A failed advance never moves the cursor; it stops playback and surfaces
 *   the server's reason.
 */

"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  ApiClientError,
  apiClients,
  type LiveSessionProjection,
  type MarketViewport as MarketViewportPayload,
} from "@/clients";
import { MarketViewport } from "./MarketViewport";
import { SimulationSessionHeader } from "./SimulationSessionHeader";

/** Ticks requested per scheduler beat while playing. */
export const PLAY_TICKS_PER_BEAT = 1;

/** Delay between scheduler beats while playing, in milliseconds. */
export const PLAY_INTERVAL_MS = 1_000;

/** Rows requested from the backwards-only viewport. */
export const VIEWPORT_ROWS = 300;

/** Resolve a failure message without implying the session advanced. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The interactive session is unavailable.";
}

/** Props accepted by `InteractiveSimulationWorkspace`. */
export interface InteractiveSimulationWorkspaceProps {
  sessionId: string;
  /**
   * Called with every authoritative session projection this workspace reads.
   *
   * The docked panels must render the same server truth the header does, so
   * the workspace publishes its state rather than letting each panel keep its
   * own copy and drift.
   */
  onSessionChange?: (session: LiveSessionProjection) => void;
  children?: ReactNode;
  className?: string;
}

/** Live practice workspace with server-authoritative pacing. */
export function InteractiveSimulationWorkspace({
  sessionId,
  onSessionChange,
  children,
  className = "",
}: InteractiveSimulationWorkspaceProps): ReactNode {
  const [session, setSession] = useState<LiveSessionProjection | null>(null);
  const [viewport, setViewport] = useState<MarketViewportPayload | null>(null);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const playingRef = useRef(false);

  const stopPlaying = useCallback(() => {
    playingRef.current = false;
    setPlaying(false);
  }, []);

  const publish = useCallback(
    (next: LiveSessionProjection) => {
      setSession(next);
      onSessionChange?.(next);
    },
    [onSessionChange],
  );

  const loadViewport = useCallback(async (id: string) => {
    const response = await apiClients.simulationWorkbench.getViewport(id, {
      before: VIEWPORT_ROWS,
    });
    if (response.status === "success") {
      setViewport(response.data);
    }
  }, []);

  /** Read authoritative state; used on mount and after any reconnect. */
  const readAuthoritative = useCallback(
    async (id: string) => {
      setError(null);
      try {
        const response = await apiClients.simulationWorkbench.getLiveSession(id);
        if (response.status === "error") {
          setError(response.error.message);
          stopPlaying();
          return;
        }
        publish(response.data);
        await loadViewport(id);
      } catch (cause) {
        setError(failureMessage(cause));
        stopPlaying();
      } finally {
        setLoading(false);
      }
    },
    [loadViewport, stopPlaying, publish],
  );

  useEffect(() => {
    void readAuthoritative(sessionId);
  }, [readAuthoritative, sessionId]);

  /** Advance the session by one bounded server call. */
  const advance = useCallback(
    async (ticks: number): Promise<boolean> => {
      setBusy(true);
      setError(null);
      try {
        const response = await apiClients.simulationWorkbench.stepLiveSession(
          sessionId,
          { ticks },
        );
        if (response.status === "error") {
          setError(response.error.message);
          stopPlaying();
          return false;
        }
        publish(response.data);
        await loadViewport(sessionId);
        return true;
      } catch (cause) {
        setError(failureMessage(cause));
        stopPlaying();
        return false;
      } finally {
        setBusy(false);
      }
    },
    [sessionId, loadViewport, stopPlaying, publish],
  );

  const seek = useCallback(
    async (targetCursor: number) => {
      setBusy(true);
      setError(null);
      try {
        const response = await apiClients.simulationWorkbench.seekLiveSession(
          sessionId,
          { target_cursor: targetCursor },
        );
        if (response.status === "error") {
          setError(response.error.message);
          return;
        }
        publish(response.data);
        await loadViewport(sessionId);
      } catch (cause) {
        setError(failureMessage(cause));
      } finally {
        setBusy(false);
      }
    },
    [sessionId, loadViewport, publish],
  );

  // Pacing scheduler: one bounded advance per beat while playing.
  useEffect(() => {
    if (!playing) return undefined;
    let cancelled = false;
    const timer = setInterval(() => {
      if (cancelled || !playingRef.current) return;
      void advance(PLAY_TICKS_PER_BEAT).then((advanced) => {
        if (!advanced) {
          stopPlaying();
        }
      });
    }, PLAY_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [playing, advance, stopPlaying]);

  // A backgrounded tab must not keep advancing a session nobody is watching.
  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        stopPlaying();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [stopPlaying]);

  // Regaining connectivity reads authoritative state before anything resumes.
  useEffect(() => {
    const onOnline = () => {
      stopPlaying();
      void readAuthoritative(sessionId);
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [readAuthoritative, sessionId, stopPlaying]);

  const play = useCallback(() => {
    playingRef.current = true;
    setPlaying(true);
  }, []);

  return (
    <section
      className={`simulation-interactive ${className}`.trim()}
      aria-label="Interactive simulation workspace"
    >
      <SimulationSessionHeader
        session={session}
        playing={playing}
        busy={busy}
        onPlay={play}
        onPause={stopPlaying}
        onStep={(ticks) => void advance(ticks)}
        onSeek={(target) => void seek(target)}
      />

      {loading ? <p role="status">Loading session state…</p> : null}
      {error ? (
        <div role="alert" className="simulation-interactive__alert">
          {error}
        </div>
      ) : null}

      <MarketViewport viewport={viewport} />

      {children}
    </section>
  );
}
